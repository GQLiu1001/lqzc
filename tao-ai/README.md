   # tao-ai · 陶选到家智能体执行平台

> 基于 LangChain / LangGraph 构建的 **多 Agent 任务编排运行时**，为陶选到家电商业务（订单、库存、优惠券、配送、售后）提供"意图理解 → 知识检索 → 工具执行 → 人机审批 → 轨迹回放"的完整链路。
> 该项目是 lqzc（Java/Spring AI 版）电商平台中 **客服 / 运维智能体** 模块的独立 Python 重构版，聚焦于"**智能体运行时**"工程化落地与可观测治理。

---

## 1. 项目目标

| 维度 | 目标 |
| --- | --- |
| 业务 | 以一个运行时承载多个业务域 Agent（客服 FAQ、仓储查询、售后审批等），对外暴露统一 Chat / Task API |
| 架构 | **Supervisor + SubAgent 独立子图**，主 Agent 只做路由 / 审批 / 汇总，子 Agent 独立承载业务能力，任务中断可恢复、可 replay |
| 范式 | **固定管线子图 + ReAct 子图** 双形态共存：客服 / 仓储走 `retrieve→plan→(approval)→execute→reflect` 管线，通用问答走 `create_react_agent` 的 Thought→Action→Observation 自主循环 |
| 能力 | 打通 **RAG（Milvus）+ MCP Tool（调用 Java 端 Spring Boot 服务）+ Human-in-the-loop 审批**，形成 Tool 执行闭环 |
| 工程 | 任务 / 审批 / 工具轨迹持久化到 MySQL；Prometheus + Grafana 观测节点耗时、工具成功率、召回率、异常告警 |
| 目标读者 | 作为简历项目，覆盖 LangChain 官方核心概念（Agents / Tools / MCP / Subagents / Handoffs / **ReAct** / HITL / Memory / Retrieval / Streaming / Structured Output / Guardrails / Router 等） |

---

## 2. 业务场景示例

1. **客服问答**：用户问"我的订单 12345 为什么还没发货？" → Supervisor 路由到 `customer_service` 子图 → 先 RAG 命中发货时效 FAQ → 再调用 MCP `order.query` 工具 → 结构化回包。
2. **优惠券售后**：用户要求"退款 + 补发一张优惠券" → Supervisor 识别为高风险动作 → 调用 `refund.apply` 与 `coupon.grant` 前挂起 `approval_tool` → 人/主 Agent 审批通过后执行 → 幂等落库 + 回执。
3. **仓储自查**：运营问"A 仓 SKU 9527 近 7 天出库量" → 路由到 `warehouse` 子图 → MCP `inventory.metric` → 结构化输出 + 图表链接。

---

## 3. 技术栈

- **编排层**：LangChain 最新版本 / LangGraph 最新版本（StateGraph、Checkpointer、Subgraph、Interrupt、`prebuilt.create_react_agent`）
- **模型层**：Ollama 本地推理（qwen3:8b / qwen3-embedding:8b），通过 `langchain-ollama` 统一封装；支持在 `ChatModel` / `EmbeddingModel` 层做 Provider 切换
- **服务层**：FastAPI + Uvicorn，SSE / WebSocket 流式输出
- **工具层**：MCP Client 接入 Java 端 `lqzc-mcp-server`（订单、库存、优惠券、配送、会员等域服务）
- **存储层**：MySQL（会话、任务、审批、工具调用轨迹、评测数据集）+ Milvus（多域知识库，按 collection 隔离）
- **可观测**：Prometheus（`/metrics` + 自定义指标）+ Grafana（面板）+ Prometheus Alert Rules + 结构化 JSON 日志
- **评测**：内置 `app/eval` 回放 + 指标统计 + `/eval/regression` 回归 gating

---

## 4. 架构总览

```
            ┌──────────────────────────────────────────────────────┐
            │                  FastAPI (routes_*)                  │
            │ /chat /task /eval /replay /metrics (Streaming)         │
            └───────────────┬───────────────────────┬──────────────┘
                            │                       │
                ┌───────────▼──────────┐   ┌────────▼─────────┐
                │  SupervisorWorkflow  │   │  ApprovalWorkflow │
                │  (主 Agent / Router) │   │  (HITL interrupt) │
                └─────┬──────┬─────────┘   └────────┬─────────┘
                      │      │                      │
         ┌────────────▼─┐  ┌─▼────────────┐   ┌─────▼────────┐
         │ CustomerSvc  │  │  Warehouse   │   │   QA ReAct   │
         │  SubAgent    │  │  SubAgent    │   │  SubAgent    │
         │ (固定管线)   │  │ (固定管线)   │   │ (ReAct 循环) │
         └─┬──────┬─────┘  └──┬────────┬──┘   └──────┬───────┘
           │      │           │        │
     ┌─────▼──┐ ┌─▼────┐  ┌───▼───┐ ┌──▼────┐
     │ RAG    │ │ MCP   │  │ RAG   │ │ MCP   │
     │ Tool   │ │ Tool  │  │ Tool  │ │ Tool  │
     └───┬────┘ └──┬────┘  └───┬───┘ └──┬────┘
         │         │            │        │
    ┌────▼────┐ ┌──▼──────────────▼──┐ ┌─▼────────────────┐
    │ Milvus  │ │  Java lqzc 服务群  │ │  MySQL 任务底座  │
    │ (多域)  │ │  (订单/库存/券/... )│ │  任务/审批/轨迹  │
    └─────────┘ └────────────────────┘ └──────────────────┘
```

**关键设计**

1. **Supervisor 主编排 + 主审批**：主 Agent 负责意图识别、Skill 命中判断、子图分发（Handoff）、风险动作拦截、最终回答汇总。审批采用 **AI 自审 + 规则兜底** 模式：简单动作由主 Agent 直接审；命中高风险清单（退款 / 发券 / 改地址等）强制走 HITL 人工审批节点。
2. **SubAgent 独立子图**：每个业务域是一张完整的 `StateGraph`，拥有自己的 prompt、tools、memory namespace，通过 `Send` / `Command(goto=...)` 进行 handoff；子图的 checkpoint 独立保存，支持**任务中断后从子图断点恢复**。子图形态分两类：
   - **固定管线子图**（`customer_service` / `warehouse`）：`retrieve → plan → (approval) → execute → reflect` 明确步骤，所有 Tool 调用经 `action_executor` 幂等落库，适合写操作 / 高风险场景。
   - **ReAct 子图**（`qa_react`）：`langgraph.prebuilt.create_react_agent`，LLM 在 Thought→Action→Observation 循环中自主决定调用哪个只读工具，适合"跨域组合式问答"。通过 Router Skill 分派，两种形态共存互补。
3. **Tool 闭环**：所有 Tool 调用经 `action_executor` 统一进出 — 审批前拦截 → 写入 `pending_actions` → 审批通过 → 幂等 key (`task_id + tool + args_hash`) 去重 → 执行 → 结构化轨迹落库。
4. **Memory 双层**：短期记忆用 LangGraph Checkpointer（会话 thread）；长期记忆用 MySQL `task_memory` + Milvus 语义索引，跨会话召回。
5. **Streaming & Structured Output**：FastAPI SSE 向前端流式推送节点事件（`node_start / token / tool_call / approval_required / final`）；所有 Tool 返回均走 Pydantic Schema，保证强约束。

---

## 5. 项目结构

```
tao-ai/
├── app/
│   ├── main.py                     # FastAPI 入口，挂载路由、lifespan、observability
│   ├── config.py                   # Settings（pydantic-settings，读取 .env）
│   ├── logging_config.py           # 结构化 JSON 日志 + trace_id
│   │
│   ├── api/                        # HTTP 层
│   │   ├── deps.py                 #   依赖注入（DB session / LLM / Retriever）
│   │   ├── routes_chat.py          #   /chat   流式对话（SSE）
│   │   ├── routes_task.py          #   /task   异步任务 CRUD / 审批
│   │   ├── routes_eval.py          #   /eval   数据集跑批、指标查询
│   │   └── routes_replay.py        #   /replay trace 回放/可视化数据
│   │
│   ├── agents/                     # Agent 定义（prompt + 绑定 tools）
│   │   ├── supervisor/agent.py     #   主 Agent：路由、审批、汇总
│   │   ├── customer_service/       #   客服子 Agent（固定管线）
│   │   ├── warehouse/              #   仓储子 Agent（固定管线）
│   │   └── qa_react/               # ★ M7: QA ReAct 子 Agent（ReAct 循环）
│   │
│   ├── workflows/                  # LangGraph StateGraph 定义
│   │   ├── supervisor_workflow.py  #   主图：guardrail + router + handoff + summarize
│   │   ├── customer_service_workflow.py  # 客服子图：retrieve→plan→approval_check→execute→reflect
│   │   ├── warehouse_workflow.py         # 仓储子图：retrieve→plan→execute→reflect
│   │   ├── qa_react_workflow.py          # ★ M7: ReAct 子图，prebuilt.create_react_agent 驱动
│   │   └── shared_nodes.py         #   通用节点：guardrail、truncate、safe_dump
│   │
│   ├── tools/
│   │   ├── action_executor.py                # ★ M2: 幂等执行器 (idempotency_key 去重)
│   │   ├── rag_tools/retriever_tool.py       # Milvus 检索 + rerank
│   │   ├── mcp_tools/client.py               # MCP 客户端 (M1 stub / M2+ real)
│   │   └── mcp_tools/lqzc_tools.py           # ★ M2: 5 工具 (order_query + refund + coupon + address + inventory)
│   │
│   ├── retrieval/                  # RAG 组件
│   │   ├── milvus_client.py        #   连接池
│   │   ├── collections.py          #   多域 collection schema
│   │   ├── indexing.py             #   切分 + 向量化入库
│   │   ├── filters.py              #   元数据过滤 DSL
│   │   ├── reranker.py             #   bge-reranker / 规则重排
│   │   └── retriever_factory.py    #   按 skill 构造 Retriever
│   │
│   ├── memory/                     # 记忆层
│   │   ├── memory_store.py         #   ★ M2: Checkpointer 工厂 (InMemorySaver / AIOMySQLSaver)
│   │   ├── db.py                   #   ★ M2: aiomysql 连接池
│   │   └── task_repo.py            #   ★ M2: Task / ToolCall / Approval CRUD
│   │
│   ├── models/                     # 模型 Provider 抽象
│   │   ├── factory.py              #   按 config 返回 chat / embedding
│   │   ├── ollama_provider.py
│   │   ├── chat.py / embedding.py
│   │
│   ├── schemas/                    # Pydantic 契约
│   │   ├── api.py / session.py / task.py / tool.py / agent_output.py
│   │   └── approval.py             #   ★ M2: PlannedAction / ApprovalRecord / ApprovalRequest
│   │
│   ├── observability/              # Prometheus 指标
│   │   ├── __init__.py
│   │   └── metrics.py              #   HTTP / Tool / Approval / Task / RAG 指标
│   │
│   └── eval/                       # 离线评测
│       ├── datasets/*.jsonl        #   基线问答集（客服 / 仓储 / 冒烟）
│       ├── runner.py               #   回放执行器
│       ├── metrics.py              #   命中率 / BLEU / 工具成功率
│       ├── replay.py               #   基于 checkpoint 的 trace 回放
│       └── report.py               #   Markdown / JSON 报告
│
├── sql/
│   └── tao_ai.sql                  # ★ M2: task / tool_call / approval 表 DDL
│
├── ops/
│   ├── grafana/
│   │   └── dashboards/
│   │       └── tao-ai-runtime-overview.json   # Grafana 预置仪表盘
│   └── prometheus/
│       ├── prometheus.yml          # 抓取 tao-ai /metrics 的配置
│       └── rules/
│           └── tao-ai-alerts.yml   # 告警规则（错误率/审批积压/延迟）
│
├── data/uploads/                   # 知识库源文件落地目录
├── pyproject.toml
└── README.md
```

---

## 6. 核心流程（以客服退款为例）

```
User ──> /chat (SSE) ──> SupervisorWorkflow
         │
         ├─ guardrail（敏感词 / PII 拦截）
         ├─ router: LLM + skill_hit(embedding 相似度) → "customer_service"
         ├─ Command(goto="customer_service_subgraph")
         │     │
         │     ├─ plan: 解构子任务（查订单 → 查退款策略 → 发起退款）
         │     ├─ retrieve: RAG Tool 查 FAQ / 政策文档（Milvus + rerank）
         │     ├─ act: MCP Tool `order.query` → `refund.apply`
         │     │       └── action_executor: 命中高风险 → interrupt
         │     └─ reflect: 结构化输出（Pydantic）
         │
         ├─ approval_workflow: 主 Agent 审批 / 人工审批
         │     └─ resume ──> action_executor.execute（幂等）
         │
         └─ summarize: 汇总为用户回复（stream tokens）
```

**可恢复性**：每一步进入 Checkpointer（MySQL），任务中断 / 重启后凭 `task_id` 从断点继续；审批态的任务以 `status=waiting_approval` 保存，审批回执触发 `graph.resume()`。

---

## 7. LangChain / LangGraph 概念映射

| 官方概念 | 在本项目中的落点 |
| --- | --- |
| **Agents** | `app/agents/*` 每个业务域 Agent |
| **Multi-agent / Subagents / Handoffs** | Supervisor ↔ 子图，用 `Command(goto=...)` / `Send` 切换 |
| **ReAct Agent** | `workflows/qa_react_workflow.py` 用 `langgraph.prebuilt.create_react_agent` 跑 Thought→Action→Observation 循环，绑定只读 MCP / RAG 工具 |
| **Prebuilt agents** | 同上，直接复用 `langgraph.prebuilt` 避免重写 tool-calling loop |
| **Router** | Supervisor 的 `router_node`（LLM + `with_structured_output(RouterDecision)`） |
| **Custom workflow** | `workflows/*` 的 StateGraph |
| **Tools** | `tools/*`（RAG / MCP / Approval 三类） |
| **Model Context Protocol (MCP)** | `mcp_tools/client.py` 接 Java `lqzc-mcp-server` |
| **Human-in-the-loop** | `approval_workflow.py` + `interrupt()` + FastAPI 审批接口 |
| **Short-term memory** | LangGraph Checkpointer（MySQL） |
| **Long-term memory** | `task_memory` 表 + Milvus 事实索引 |
| **Retrieval** | `retrieval/*` + `rag_tools` |
| **Structured output** | 全链路 Pydantic Schema（`schemas/*`） |
| **Streaming** | FastAPI SSE / LangGraph `astream_events` |
| **Guardrails** | `shared_nodes.guardrail` + 工具白名单 + 审批拦截 |
| **Runtime context engineering** | `deps.py` + `RunnableConfig` 注入 tenant / user / trace_id |
| **Skills** | Supervisor 的 skill 命中表 + 对应子图 |
| **Messages** | `schemas/session.Message` 统一入库格式 |

---

## 8. 期望达成的效果

- ✅ 单一 Python 运行时承载 **≥3 个业务域 SubAgent**，主/子图可独立演进。
- ✅ 任务级 **Checkpoint 断点恢复**，审批挂起 / 恢复 < 1s。
- ✅ Tool 执行 **幂等率 100%**（同 `task_id + args_hash` 不重复执行），冲突有结构化错误码。
- ✅ RAG 基线 **Recall@5 ≥ 0.85**（客服 FAQ 数据集），rerank 后 top1 命中率提升 ≥ 15%。
- ✅ 已落地 Prometheus 指标 + 告警规则（工具错误率、审批积压、HTTP P95 延迟），Grafana 可直接接入绘制面板。
- ✅ `eval` 目录可一键回放基线集，输出 Markdown 报告，便于回归。
- ✅ 已提供 `/replay` 会话/任务回放接口，与 `/eval/regression` 回归阈值检查。

---

## 9. 可观测接入（Docker Prometheus + Grafana）

> 适配你的当前部署：Prometheus/Grafana 在 Docker，`tao-ai` 跑在宿主机 `:8000`。

### 9.1 指标端点

服务启动后可访问：

```bash
curl http://localhost:8000/metrics
```

若看到 `tao_http_requests_total`、`tao_tool_calls_total` 等指标即正常。

### 9.2 Prometheus 配置

仓库已提供配置文件：

- `ops/prometheus/prometheus.yml`
- `ops/prometheus/rules/tao-ai-alerts.yml`

`prometheus.yml` 默认抓取目标是：

```yaml
targets: ["host.docker.internal:8000"]
```

如果你的 `tao-ai` 也在 Docker 网络里，请改成对应服务名（例如 `tao-ai:8000`）。

### 9.3 启动/挂载 Prometheus

示例（仅供参考，按你的容器名调整）：

```bash
docker run -d --name tao-prometheus -p 9090:9090 \
  -v $(pwd)/ops/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v $(pwd)/ops/prometheus/rules:/etc/prometheus/rules \
  prom/prometheus
```

### 9.4 Grafana 接入

1. Data Source 选择 Prometheus，URL 指向你的 Prometheus（如 `http://prometheus:9090` 或宿主机地址）。
2. 直接导入仓库内预置仪表盘 JSON：`ops/grafana/dashboards/tao-ai-runtime-overview.json`。
3. 若你想自行扩展，新建 Dashboard 后可直接使用下列指标：
   - `tao_http_request_duration_seconds`
   - `tao_tool_calls_total`
   - `tao_tool_latency_seconds`
   - `tao_approval_required_total`
   - `tao_approval_decisions_total`
   - `tao_task_status_transitions_total`
   - `tao_rag_hits_per_query`
4. 告警规则由 Prometheus 侧加载：`TaoAiHighErrorRate` / `TaoAiApprovalBacklog` / `TaoAiP95LatencyHigh`

---

## 10. M5 目标细化

M5 聚焦在“仓储域能力扩展”，以最小可交付为准（当前已完成）：

### 10.1 已完成范围

1. 新增 `warehouse` 子图（`retrieve → plan → execute → reflect`）。
2. Supervisor 支持 `warehouse` 路由并进入子图执行。
3. 新增 3 个查询型 MCP 工具（先以 stub 形式跑通）：
   - `inventory_stock_query`
   - `logistics_query`
   - `coupon_query`

### 10.2 后续增强（不属于当前 M5 完成标准）

1. Java `lqzc-mcp-server` 提供对应真实接口（inventory/logistics/coupon 查询）。
2. Python 端将 `MCPClient.call` 从 stub 切换到真实 MCP session 调用。
3. 为仓储场景补充评测集与回归门槛（路由命中率、工具成功率、平均延迟）。

---

## 11. M7 QA ReAct 子图

M7 聚焦在"范式补齐"——让运行时同时具备**固定管线**和 **ReAct 自主循环**两种 Agent 形态，以对照方式覆盖 LangChain / LangGraph 官方推荐的核心 Agent 范式。

### 11.1 已完成范围

1. 新增 `qa_react` 子图（`app/workflows/qa_react_workflow.py`），基于 `langgraph.prebuilt.create_react_agent`。
2. Supervisor Router 扩展 skill 枚举并新增 `qa_react` 分支；命中后以 compiled subgraph 形式进入 ReAct 循环。
3. 只读工具集（`rag_search` / `order_query` / `inventory_stock_query` / `inventory_metric` / `logistics_query` / `coupon_query`）绑定到 ReAct Agent；高风险写操作仍只走 `customer_service` 的三级审批链路。
4. `/chat` SSE 新增 `prepare` / `react` 节点事件；任务状态入 `task` 表，Prometheus `tao_task_status_transitions_total{skill="qa_react"}` 可观测。
5. README §7 概念映射补齐 `ReAct Agent` / `Prebuilt agents` 两项。

### 11.2 固定管线 vs. ReAct 对照

| 维度 | 固定管线子图（customer_service / warehouse） | ReAct 子图（qa_react） |
| --- | --- | --- |
| 控制流 | 图结构硬编码（`retrieve → plan → approval → execute → reflect`） | LLM 在 Thought → Action → Observation 中自主决定下一步 |
| 工具调用 | 经 `action_executor` 幂等落库，写操作受审批 | `ToolNode` 直连，只读工具，无审批 |
| 适用场景 | 流程明确 / 有写操作 / 需要可追溯的动作序列 | 跨域组合式查询 / 流程无法提前定死 |
| 对话风格 | 任务式，一问一答 | 探索式，允许多轮工具调用 |
| 观测 | `task/tool_call/approval` 三张表 + tool 指标 | `task` 表 + `react_iterations` / `react_tools_used` |

### 11.3 后续增强

1. 把 ReAct Agent 的每一次工具调用也接进 `action_executor`，使其 latency / 成功率能在同一指标维度聚合。
2. 为 ReAct 专门准备 `eval/datasets/qa_react.jsonl`，以"工具调用次数 + 最终正确率"作为回归门槛。
3. 探索 `pre_model_hook` / `post_model_hook` 实现会话级上下文裁剪与结果 Guardrail。

---

## 12. 路线图

- [x] M1：Supervisor + CustomerService 子图跑通 + MCP 最小工具集 *(2026-04-15)*
- [x] M2：三级审批 HITL + MySQL Checkpointer + 幂等执行器 + Task API *(2026-04-16)*
- [x] M3：Milvus 多域知识库 + rerank + `/eval` 基线
- [x] M4（基础版）：Prometheus 指标 + `/metrics` + Alert Rules + Grafana 可接入 *(2026-04-16)*
- [x] M5：Warehouse 子图 + 查询型 MCP 工具（stub 跑通）*(2026-04-16)*
- [x] M6（基础版）：`/replay` 回放 + `/eval/regression` 线上回归 gating *(2026-04-16)*
- [x] M7：QA ReAct 子图（`create_react_agent` + 只读工具集），与固定管线子图共存 *(2026-04-16)*

---

## 13. 与 lqzc (Java/Spring AI) 项目的关系

lqzc 主站（Java）通过 `lqzc-mcp-server` 将**订单 / 库存 / 优惠券 / 配送 / 会员**等能力以 MCP 协议对外暴露；tao-ai 作为**独立 Python 智能体运行时**消费这些 MCP 工具，不直接访问业务 DB，保证**边界清晰、权限可控**。
