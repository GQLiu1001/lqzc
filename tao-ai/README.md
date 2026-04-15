# tao-ai · 陶选到家智能体执行平台

> 基于 LangChain / LangGraph 构建的 **多 Agent 任务编排运行时**，为陶选到家电商业务（订单、库存、优惠券、配送、售后）提供"意图理解 → 知识检索 → 工具执行 → 人机审批 → 轨迹回放"的完整链路。
> 该项目是 lqzc（Java/Spring AI 版）电商平台中 **客服 / 运维智能体** 模块的独立 Python 重构版，聚焦于"**智能体运行时**"工程化落地与可观测治理。

---

## 1. 项目目标

| 维度 | 目标 |
| --- | --- |
| 业务 | 以一个运行时承载多个业务域 Agent（客服 FAQ、仓储查询、售后审批等），对外暴露统一 Chat / Task API |
| 架构 | **Supervisor + SubAgent 独立子图**，主 Agent 只做路由 / 审批 / 汇总，子 Agent 独立承载业务能力，任务中断可恢复、可 replay |
| 能力 | 打通 **RAG（Milvus）+ MCP Tool（调用 Java 端 Spring Boot 服务）+ Human-in-the-loop 审批**，形成 Tool 执行闭环 |
| 工程 | 任务 / 审批 / 工具轨迹持久化到 MySQL；Prometheus + Grafana 观测节点耗时、工具成功率、召回率、异常告警 |
| 目标读者 | 作为简历项目，覆盖 LangChain 官方核心概念（Agents / Tools / MCP / Subagents / Handoffs / HITL / Memory / Retrieval / Streaming / Structured Output / Guardrails / Router 等） |

---

## 2. 业务场景示例

1. **客服问答**：用户问"我的订单 12345 为什么还没发货？" → Supervisor 路由到 `customer_service` 子图 → 先 RAG 命中发货时效 FAQ → 再调用 MCP `order.query` 工具 → 结构化回包。
2. **优惠券售后**：用户要求"退款 + 补发一张优惠券" → Supervisor 识别为高风险动作 → 调用 `refund.apply` 与 `coupon.grant` 前挂起 `approval_tool` → 人/主 Agent 审批通过后执行 → 幂等落库 + 回执。
3. **仓储自查**：运营问"A 仓 SKU 9527 近 7 天出库量" → 路由到 `warehouse` 子图 → MCP `inventory.metric` → 结构化输出 + 图表链接。

---

## 3. 技术栈

- **编排层**：LangChain 0.3 / LangGraph 0.2（StateGraph、Checkpointer、Subgraph、Interrupt）
- **模型层**：Ollama 本地推理（qwen2.5 / bge-m3 embedding），通过 `langchain-ollama` 统一封装；支持在 `ChatModel` / `EmbeddingModel` 层做 Provider 切换
- **服务层**：FastAPI + Uvicorn，SSE / WebSocket 流式输出
- **工具层**：MCP Client 接入 Java 端 `lqzc-mcp-server`（订单、库存、优惠券、配送、会员等域服务）
- **存储层**：MySQL（会话、任务、审批、工具调用轨迹、评测数据集）+ Milvus（多域知识库，按 collection 隔离）
- **可观测**：Prometheus（自定义 metrics）+ Grafana（面板 / 告警）+ 结构化 JSON 日志
- **评测**：内置 `app/eval` 回放 + 指标统计（命中率、工具成功率、平均耗时）

---

## 4. 架构总览

```
            ┌──────────────────────────────────────────────────────┐
            │                  FastAPI (routes_*)                  │
            │   /chat  /task  /eval  /files  /admin (Streaming SSE)│
            └───────────────┬───────────────────────┬──────────────┘
                            │                       │
                ┌───────────▼──────────┐   ┌────────▼─────────┐
                │  SupervisorWorkflow  │   │  ApprovalWorkflow │
                │  (主 Agent / Router) │   │  (HITL interrupt) │
                └─────┬──────┬─────────┘   └────────┬─────────┘
                      │      │                      │
         ┌────────────▼─┐  ┌─▼────────────┐   ┌─────▼────────┐
         │ CustomerSvc  │  │  Warehouse   │   │   ...更多    │
         │  SubAgent    │  │  SubAgent    │   │  业务子图    │
         │ (独立子图)   │  │ (独立子图)   │   │              │
         └─┬──────┬─────┘  └──┬────────┬──┘   └──────────────┘
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
2. **SubAgent 独立子图**：每个业务域是一张完整的 `StateGraph`，拥有自己的 prompt、tools、memory namespace，通过 `Send` / `Command(goto=...)` 进行 handoff；子图的 checkpoint 独立保存，支持**任务中断后从子图断点恢复**。
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
│   │   ├── routes_files.py         #   /files  知识库文件上传 / 切分 / 入库
│   │   └── routes_admin.py         #   /admin  Agent / Tool / 索引 管理
│   │
│   ├── agents/                     # Agent 定义（prompt + 绑定 tools）
│   │   ├── supervisor/agent.py     #   主 Agent：路由、审批、汇总
│   │   ├── customer_service/       #   客服子 Agent
│   │   └── warehouse/              #   仓储子 Agent
│   │
│   ├── workflows/                  # LangGraph StateGraph 定义
│   │   ├── supervisor_workflow.py  #   主图：router + handoff + approval
│   │   ├── domain_subworkflow.py   #   子图通用骨架（plan → retrieve → act → reflect）
│   │   ├── customer_service_workflow.py
│   │   ├── warehouse_workflow.py
│   │   ├── approval_workflow.py    #   HITL 子图（interrupt + resume）
│   │   └── shared_nodes.py         #   通用节点：guardrail、summarize、error_handler
│   │
│   ├── tools/
│   │   ├── rag_tools/retriever_tool.py       # Milvus 检索 + rerank
│   │   ├── mcp_tools/client.py               # MCP 客户端初始化
│   │   ├── mcp_tools/lqzc_tools.py           # 订单/库存/券/配送 工具封装
│   │   └── approval_tools/
│   │       ├── approval_tool.py              # 审批挂起 / 恢复
│   │       └── action_executor.py            # 幂等执行 + 轨迹落库
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
│   │   ├── memory_store.py         #   统一抽象
│   │   ├── mysql_store.py          #   LangGraph Checkpointer (MySQL)
│   │   ├── session_memory.py       #   短期 (thread)
│   │   └── task_memory.py          #   长期 (跨任务事实)
│   │
│   ├── models/                     # 模型 Provider 抽象
│   │   ├── factory.py              #   按 config 返回 chat / embedding
│   │   ├── ollama_provider.py
│   │   ├── chat.py / embedding.py
│   │
│   ├── schemas/                    # Pydantic 契约
│   │   ├── api.py / session.py / task.py / approval.py
│   │   ├── tool.py / retrieval.py / agent_output.py / eval.py
│   │
│   ├── observability/metrics.py    # Prometheus 指标（节点耗时、工具 QPS、召回率…）
│   │
│   └── eval/                       # 离线评测
│       ├── datasets/*.jsonl        #   基线问答集（客服 / 仓储 / 冒烟）
│       ├── runner.py               #   回放执行器
│       ├── metrics.py              #   命中率 / BLEU / 工具成功率
│       ├── replay.py               #   基于 checkpoint 的 trace 回放
│       └── report.py               #   Markdown / JSON 报告
│
├── sql/
│   ├── tao_ai.sql                  # 初始化：sessions / tasks / messages / actions
│   └── migrations/                 # 增量脚本（eval 表、action_executions 表…）
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
| **Router** | Supervisor 的 `router_node`（LLM + skill embedding） |
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
- ✅ Grafana 面板覆盖：节点 P95 耗时、工具成功率、审批等待时长、LLM token 消耗、异常告警。
- ✅ `eval` 目录可一键回放基线集，输出 Markdown 报告，便于回归。

---

## 9. 快速开始

```bash
# 1. 依赖
uv sync            # 或 pip install -e .

# 2. 基础设施
docker compose up -d mysql milvus prometheus grafana
mysql < sql/tao_ai.sql
mysql < sql/migrations/002_add_eval_tables.sql
mysql < sql/migrations/003_add_action_executions.sql

# 3. 本地模型
ollama pull qwen2.5:7b
ollama pull bge-m3

# 4. 启动
cp .env.example .env
uvicorn app.main:app --reload --port 8088

# 5. 冒烟
curl -N -X POST localhost:8088/chat \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"s1","message":"订单12345为什么没发货"}'
```

---

## 10. 路线图

- [ ] M1：Supervisor + CustomerService 子图跑通 + MCP 最小工具集
- [ ] M2：Approval 子图 + MySQL 轨迹 + 幂等执行器
- [ ] M3：Milvus 多域知识库 + rerank + `/eval` 基线
- [ ] M4：Prometheus 指标全量 + Grafana 面板 + 告警
- [ ] M5：Warehouse 子图 + 更多 MCP 工具（优惠券、配送）
- [ ] M6：Replay / Trace 可视化 + 线上回归

---

## 11. 与 lqzc (Java/Spring AI) 项目的关系

lqzc 主站（Java）通过 `lqzc-mcp-server` 将**订单 / 库存 / 优惠券 / 配送 / 会员**等能力以 MCP 协议对外暴露；tao-ai 作为**独立 Python 智能体运行时**消费这些 MCP 工具，不直接访问业务 DB，保证**边界清晰、权限可控**。
