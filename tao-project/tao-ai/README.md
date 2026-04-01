# agent-runtime

Python 侧智能编排运行时。
该项目作为 Java 业务系统之上的 **Agent Runtime** 存在，负责多 Agent 编排、技能路由、RAG 检索、审批流控制、会话记忆、评估与可观测性。

> 核心原则：
> **Java 负责业务真相与状态变更，Python 负责智能决策与流程编排。**

------

## 1. 项目定位

`agent-runtime` 是一个基于 **LangChain + LangGraph + Milvus + Ollama** 的智能运行时系统，用于承接以下能力：

- 多 Agent 协作
- 业务 Skill 编排
- 基于企业知识的 RAG 检索
- MCP Tool 调用
- 审批流与高风险动作拦截
- 多轮会话记忆
- Agent 评估、回放与观测

该项目不直接承担企业主业务数据库写入，也不替代 Java 后端。
所有涉及订单、库存、售后、权限、审计、状态修改等核心业务动作，统一通过 Java 侧暴露的 MCP / HTTP 能力完成。

------

## 2. 技术栈

### 核心框架

- **LangChain**：统一模型、工具、检索、结构化输出与组件抽象
- **LangGraph**：负责有状态工作流、Agent 编排、持久化恢复、人工中断与审批节点
- **Milvus**：向量数据库，承载文档、案例、规则、知识片段索引
- **Ollama**：本地模型运行时，提供 chat model 与 embedding model
- **FastAPI**：对外提供 Python 侧 Agent API
- **Pydantic**：输入输出、状态对象、Tool Schema、Skill Schema 定义
- **MySQL**：会话状态、任务状态、审批记录、审计日志

### 选型理由

- LangChain 提供面向 agent 与 LLM 应用的统一抽象和组件集成能力
- LangGraph 更适合做 Supervisor、多 Agent、有状态长流程与审批式工作流
- Milvus 适合企业知识检索、案例库检索、规则库检索与规模化向量搜索
- Ollama 可以本地运行模型，且 LangChain 官方已有正式集成

------

## 3. 项目目标

本项目最终提供以下能力：

1. 接收业务请求并判断应由哪个 Agent / Skill 处理
2. 根据用户问题调用 Java 侧 MCP 工具获取业务事实
3. 从 Milvus 检索企业知识、案例、流程与政策文档
4. 生成结构化决策结果、建议、解释或回复草稿
5. 对高风险动作自动进入审批流
6. 保存任务状态，支持中断恢复、重试与审计
7. 为客服、仓储、运营等业务域提供可扩展的智能执行能力

------

## 4. 项目结构

```text
agent-runtime/
  app/
    api/
    agents/
      supervisor/
      customer_service/
      warehouse/
    skills/
      customer/
      warehouse/
    tools/
      mcp_tools/
      rag_tools/
      approval_tools/
    workflows/
    memory/
    models/
    retrieval/
    schemas/
    eval/
  tests/
  scripts/
```

------

## 5. 目录说明

### `app/api/`

对外 API 层。

职责：

- 提供 HTTP 接口
- 接收用户请求、上下文、会话 ID、租户信息
- 输出统一响应格式
- 提供健康检查、诊断、调试、回放接口

建议包含：

- `routes_chat.py`
- `routes_task.py`
- `routes_admin.py`
- `routes_eval.py`
- `deps.py`

典型接口：

- `POST /chat`
- `POST /tasks/execute`
- `POST /tasks/approve`
- `GET /tasks/{task_id}`
- `GET /sessions/{session_id}`
- `POST /eval/run`
- `GET /health`

------

### `app/agents/`

Agent 层，定义不同业务域的智能角色。

#### `app/agents/supervisor/`

总控 Agent。

职责：

- 接受用户请求
- 判断请求属于 FAQ、客服、仓储、审批还是转人工
- 路由到对应 skill / sub-agent / workflow
- 聚合多个工具或多个 Agent 的结果
- 控制全局策略与风控边界

这是系统主入口，不直接做底层业务写入。

#### `app/agents/customer_service/`

客服 Agent。

职责：

- 处理订单查询、退款咨询、售后受理、物流解释
- 生成客服话术和回复草稿
- 调用订单、物流、售后 MCP 工具
- 调用客服知识库、政策库、FAQ 库

#### `app/agents/warehouse/`

仓储 Agent。

职责：

- 处理库存查询、仓储 SOP 检索、异常库存解释
- 生成库存冻结/释放建议
- 调用库存、仓位、仓储任务类 MCP 工具
- 调用仓储知识库、异常案例库

------

### `app/skills/`

Skill 层，定义“可复用的业务处理套路”。

Skill 不是单纯 prompt 模板，而是一个完整的业务能力单元，包含：

- 适用场景
- 依赖工具
- 检索策略
- 输出格式
- 风险级别
- 是否需要审批
- 失败兜底逻辑

#### `app/skills/customer/`

建议包含：

- `order_status_explain_skill.py`
- `refund_policy_skill.py`
- `after_sale_intake_skill.py`
- `customer_reply_draft_skill.py`

#### `app/skills/warehouse/`

建议包含：

- `inventory_exception_skill.py`
- `warehouse_sop_retrieval_skill.py`
- `stock_hold_release_skill.py`
- `replenishment_suggestion_skill.py`

------

### `app/tools/`

工具层，负责把外部能力包装成 Agent 可调用的标准 Tool。

#### `app/tools/mcp_tools/`

Java 端暴露的 MCP 工具适配层。

职责：

- 连接 Java MCP Server
- 将业务能力封装为 LangChain Tool
- 做请求参数校验、鉴权信息透传、幂等键透传
- 将底层错误转换为统一异常

建议包含的工具：

- `get_order_detail`
- `get_order_timeline`
- `get_inventory_status`
- `get_warehouse_task_status`
- `create_after_sale_ticket`
- `submit_refund_for_approval`
- `submit_inventory_adjustment_for_approval`

#### `app/tools/rag_tools/`

知识检索相关工具。

职责：

- 查询 Milvus
- 召回 FAQ、政策、SOP、案例
- 支持 metadata filter、top-k、重排
- 输出带来源信息的证据片段

#### `app/tools/approval_tools/`

审批相关工具。

职责：

- 发起审批
- 查询审批状态
- 接收审批结果
- 将审批结果写回任务状态流

------

### `app/workflows/`

工作流层。

职责：

- 使用 LangGraph 定义完整执行图
- 串联 Agent、Skill、RAG、审批、记忆与状态转移
- 管理任务生命周期
- 支持 interrupt / resume / retry

建议包含：

- `supervisor_workflow.py`
- `customer_service_workflow.py`
- `warehouse_workflow.py`
- `approval_workflow.py`
- `shared_nodes.py`

工作流应具备以下节点类型：

- 输入解析节点
- 路由判断节点
- Tool 调用节点
- RAG 检索节点
- 风险评估节点
- 审批节点
- 输出整合节点
- 状态持久化节点

------

### `app/memory/`

记忆层。

职责：

- 管理短期会话上下文
- 管理长期任务与历史偏好
- 控制上下文压缩与摘要
- 按租户 / 用户 / 任务隔离上下文

建议拆分：

- `session_memory.py`
- `task_memory.py`
- `memory_store.py`

记忆分层：

- **Short-term memory**：当前会话、当前 ticket、当前任务
- **Long-term memory**：用户偏好、历史工单、历史异常、常见处理习惯
- **Working memory**：当前 workflow 的中间状态与工具结果

------

### `app/models/`

模型访问层。

职责：

- 封装 LangChain model init
- 屏蔽底层模型供应商差异
- 支持 Ollama chat / embedding / fallback
- 统一超时、重试、日志、token 统计

建议包含：

- `chat.py`
- `embedding.py`
- `factory.py`
- `ollama_provider.py`

默认使用：

- `ChatOllama`
- `OllamaEmbeddings`

LangChain 对 Ollama 已提供正式包级集成 。

------

### `app/retrieval/`

检索层。

职责：

- 管理 Milvus collection
- 执行索引、写入、删除、检索、重排
- 提供多知识库路由
- 管理 chunking 与 metadata 规范

建议包含：

- `milvus_client.py`
- `collections.py`
- `indexing.py`
- `retriever_factory.py`
- `reranker.py`
- `filters.py`

建议知识库拆分为：

- `customer_faq`
- `customer_policy`
- `warehouse_sop`
- `business_rules`
- `historical_cases`

Milvus 作为高性能向量数据库，适合作为本项目的向量检索底座 。

------

### `app/schemas/`

统一数据结构定义。

职责：

- 定义 API 请求与响应
- 定义 Workflow State
- 定义 Agent Output Schema
- 定义 Tool Input Schema
- 定义审批对象与任务对象

建议包含：

- `api.py`
- `task.py`
- `session.py`
- `approval.py`
- `tool.py`
- `retrieval.py`
- `agent_output.py`

统一 schema 是生产稳定性的关键。
所有 Agent 输出都应尽量结构化，避免自由文本直接驱动业务动作。

------

### `app/eval/`

评估层。

职责：

- 回放任务
- 评估路由准确率
- 评估 Tool 调用成功率
- 评估 RAG 证据质量
- 评估业务完成率与审批触发率

建议包含：

- `datasets.py`
- `runner.py`
- `metrics.py`
- `report.py`
- `replay.py`

核心指标：

- route accuracy
- tool success rate
- retrieval hit rate
- answer groundedness
- approval trigger precision
- escalation rate

------

### `tests/`

测试目录。

建议包含：

- 单元测试
- Workflow 测试
- Tool 集成测试
- RAG 检索测试
- API 测试
- 回归测试
- Prompt / Skill 测试

建议结构：

```text
tests/
  unit/
  integration/
  workflows/
  api/
  eval/
  fixtures/
```

------

### `scripts/`

辅助脚本目录。

建议包含：

- 文档入库脚本
- 索引重建脚本
- 本地开发启动脚本
- 数据回放脚本
- 批量评估脚本
- 环境诊断脚本

------

## 6. 系统能力

### 6.1 多 Agent 编排

系统采用 Supervisor 模式：

- `Supervisor Agent` 负责全局路由与调度
- `Customer Service Agent` 负责客服域问题
- `Warehouse Agent` 负责仓储域问题

后续可扩展：

- `Risk Agent`
- `Ops Agent`
- `Procurement Agent`

------

### 6.2 Skill 驱动执行

系统主要依赖 Skill 进行任务收敛。

好处：

- 比纯自由对话更稳
- 输出结构更可控
- 更容易做审批和审计
- 更适合逐步沉淀业务经验

------

### 6.3 RAG 检索

系统通过 Milvus 承载以下知识：

- FAQ
- 业务政策
- 仓储 SOP
- 历史案例
- 规则文档

RAG 输出要求：

- 返回答案
- 返回证据片段
- 返回来源 metadata
- 返回置信度或最低限度的可解释提示

------

### 6.4 MCP 工具调用

Python 不直接改业务数据库。
所有真实业务动作通过 Java 侧 MCP / HTTP 完成。

设计原则：

- 读写分离
- 写操作统一审计
- 高风险操作必须审批
- 所有副作用工具必须支持幂等

------

### 6.5 审批流

以下场景默认进入审批：

- 退款
- 补偿
- 库存冻结
- 库存释放
- 库存调整
- 敏感工单结论
- 影响订单状态的动作

审批动作：

- `approve`
- `reject`
- `edit_and_approve`

------

### 6.6 会话记忆

支持：

- 多轮会话
- ticket 级上下文
- task 级状态恢复
- 摘要压缩
- 长任务恢复

LangGraph 本身就适合用来承载这类 stateful workflow 和 memory 模式 。

------

## 7. 请求处理链路

一个典型请求的处理路径如下：

1. API 收到用户请求
2. 创建或恢复 session / task state
3. Supervisor 判断请求类型
4. 选择 Skill、RAG Tool 或子 Agent
5. 需要业务事实时调用 MCP Tool
6. 需要知识时调用 RAG Tool
7. 若动作高风险则进入审批节点
8. 审批通过后继续执行
9. 输出结果并写入任务状态
10. 记录审计日志与评估数据

------

## 8. 运行时状态模型

建议任务状态至少包含：

- `NEW`
- `ROUTED`
- `RETRIEVING`
- `TOOL_RUNNING`
- `WAITING_APPROVAL`
- `APPROVED`
- `REJECTED`
- `COMPLETED`
- `FAILED`
- `ESCALATED`

每个任务对象建议包含：

- `task_id`
- `session_id`
- `tenant_id`
- `user_id`
- `current_agent`
- `current_skill`
- `risk_level`
- `tool_trace`
- `retrieval_trace`
- `approval_trace`
- `final_response`
- `created_at`
- `updated_at`

------

## 9. 配置说明

建议使用 `.env` 管理配置。

示例：

```env
APP_NAME=agent-runtime
APP_ENV=dev
APP_PORT=8080
LOG_LEVEL=INFO
ENABLE_REQUEST_LOGGING=true
ENABLE_METRICS=true
METRICS_PATH=/metrics
METRICS_COLLECT_INTERVAL_SECONDS=5
METRICS_TASK_STUCK_SECONDS=120
METRICS_TASK_LOOP_STEP_THRESHOLD=80

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=qwen2.5:14b
OLLAMA_EMBED_MODEL=qwen3-embedding:8b

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=tao_ai_runtime
MYSQL_USER=root
MYSQL_PASSWORD=root

MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_DB=default

LQZC_BASE_URL=http://localhost:8001
LQZC_CUSTOMER_TOKEN=
LQZC_ADMIN_TOKEN=
MCP_SERVER_URL=http://localhost:9000
MCP_PROTOCOL_VERSION=2025-06-18
MCP_TIMEOUT_SECONDS=20

ENABLE_APPROVAL=true
APPROVAL_ADMIN_TOKEN=
ENABLE_TRACE=true
ENABLE_EVAL=true
ENABLE_LLM_SKILL_ROUTER=true
LLM_SKILL_ROUTER_TIMEOUT_SECONDS=12
LLM_SKILL_ROUTER_MIN_RULE_SCORE=16
```

------

## 10. API 设计

### `POST /chat`

用于处理对话请求。

请求体示例：

```json
{
  "session_id": "sess_001",
  "user_id": "u_1001",
  "tenant_id": "t_01",
  "message": "这个订单为什么还没发货？",
  "context": {
    "channel": "customer_service"
  }
}
```

响应体示例：

```json
{
  "task_id": "task_001",
  "session_id": "sess_001",
  "agent": "customer_service",
  "skill": "order_status_explain_skill",
  "answer": "订单尚未发货，原因是仓库待拣货。",
  "evidence": [
    {
      "source": "order_system",
      "content": "订单状态：待拣货"
    }
  ],
  "requires_approval": false,
  "status": "COMPLETED"
}
```

------

### `POST /tasks/approve`

处理审批动作。

当配置了 `APPROVAL_ADMIN_TOKEN` 时，请求必须携带以下任一请求头：

- `X-Approval-Token: <token>`
- `Authorization: Bearer <token>`

```json
{
  "task_id": "task_002",
  "approval_action": "approve",
  "approver_id": "admin_01",
  "comment": "同意退款"
}
```

------

### `GET /tasks/{task_id}`

获取任务状态、轨迹和当前结果。

------

### `GET /ready`

生产就绪探活接口，返回 MySQL / Milvus / Ollama 的连通状态。

------

### `POST /eval/run`

执行真实数据集回放评估（不再是 stub），支持落库。

请求体示例：

```json
{
  "dataset_name": "smoke",
  "max_cases": 20,
  "stop_on_error": false,
  "persist": true
}
```

------

### `GET /eval/datasets`

返回可用评估数据集列表（来自 `app/eval/datasets/*.jsonl`）。

------

### `GET /eval/runs`

返回历史评估运行摘要。

------

### `GET /eval/runs/{run_id}`

返回单次评估的摘要和逐 case 结果明细。

------

## 11. Milvus 设计

建议为不同业务知识建立独立 collection，而不是把所有文档塞进一个大 collection。

### 建议 collection

- `customer_faq_collection`
- `customer_policy_collection`
- `warehouse_sop_collection`
- `business_rules_collection`
- `historical_case_collection`

### 建议 metadata

- `doc_id`
- `doc_type`
- `domain`
- `source`
- `owner`
- `created_at`
- `updated_at`
- `version`
- `risk_level`
- `tags`

### 检索策略

- query rewrite
- domain routing
- metadata filtering
- dense retrieval
- reranking
- grounded response generation

------

## 12. 模型策略

默认使用本地 Ollama。

### 职责划分

- **Chat 模型**：用于问答、路由、Tool 调用、回复生成
- **Embedding 模型**：用于文档切片向量化和查询向量化

### 推荐原则

- 简单 FAQ：轻量模型
- 业务说明与草稿：通用中文模型
- 高风险工具调用：更强模型或强约束 schema
- 检索：单独 embedding 模型

### 模型适配层要求

- 统一调用入口
- 统一日志
- 统一失败重试
- 统一 schema 输出约束
- 支持后续替换云模型

------

## 13. 安全与风控

### 基本原则

- Python 不直接写业务主库
- 工具权限严格按角色区分
- 高风险动作必须审批
- 所有写操作必须幂等
- 所有任务必须有 trace
- 所有最终结论都应有事实依据或检索证据

### 风险分级

- `LOW`：FAQ、说明、文案草稿
- `MEDIUM`：建议类动作、工单创建
- `HIGH`：退款、库存调整、冻结释放
- `CRITICAL`：影响订单状态、金额、库存真值的操作

------

## 14. 可观测性

系统应至少支持以下观测数据：

- 请求级 trace
- Agent 路由结果
- Skill 命中情况
- Tool 调用耗时
- Tool 调用失败率
- RAG 检索命中率
- 审批触发率
- 最终业务完成率

可观测性应覆盖：

- API 层
- Workflow 层
- Tool 层
- Retrieval 层
- Model 层

### 14.1 Prometheus 指标

默认暴露 `GET /metrics`（可由 `METRICS_PATH` 修改）。

核心指标包括：

- `taoai_tasks_inflight`
- `taoai_tasks_started_total`
- `taoai_tasks_finished_total`
- `taoai_task_duration_seconds`
- `taoai_task_status_transition_total`
- `taoai_workflow_node_total`
- `taoai_workflow_node_duration_seconds`
- `taoai_subworkflow_dispatch_total`
- `taoai_retrieval_requests_total`
- `taoai_retrieval_hits`
- `taoai_tool_calls_total`
- `taoai_tool_call_duration_seconds`
- `taoai_process_resident_memory_bytes`
- `taoai_python_gc_objects`
- `taoai_event_loop_lag_seconds`
- `taoai_tasks_stuck`
- `taoai_task_loop_suspect_total`

Prometheus 抓取示例：

```yaml
scrape_configs:
  - job_name: tao-ai-runtime
    static_configs:
      - targets: ["127.0.0.1:8000"]
    metrics_path: /metrics
    scrape_interval: 5s
```

------

## 15. 测试策略

### 单元测试

验证：

- schema
- 工具适配
- 路由规则
- skill 逻辑
- 检索过滤器

### 集成测试

验证：

- Ollama 调用
- Milvus 检索
- MCP 工具连接
- MySQL 存储
- 完整 workflow 执行

### 回归测试

验证：

- 历史高频问题结果是否退化
- 高风险流程是否仍被正确拦截
- skill 输出结构是否稳定

### 评估测试

验证：

- route accuracy
- retrieval quality
- tool success rate
- approval precision

------

## 16. 开发规范

### 编码规范

- 所有输入输出都使用 Pydantic schema
- 所有 tool 都必须显式定义 input schema
- 所有 workflow node 都必须可追踪
- 所有高风险路径都必须记录 approval trace
- 所有 skill 都要有统一输出结构

### Prompt / Skill 规范

- 不把大量业务规则直接堆到 system prompt
- 规则优先放在 skill 配置和 RAG 文档中
- 输出必须尽量结构化
- 拒绝无证据的业务断言

### Tool 规范

- 能读不写
- 能申请不直改
- 能草稿不提交
- 所有写动作必须幂等
- 所有错误必须转换为统一异常对象

------

## 17. 适用业务场景

本项目默认覆盖以下场景：

### 客服域

- 订单状态解释
- 物流异常说明
- 退款政策解释
- 售后受理
- 回复草稿生成

### 仓储域

- 库存查询
- 仓储 SOP 检索
- 异常库存说明
- 库存冻结 / 释放建议
- 补货建议

### 平台管理域

- 审批流
- 风险控制
- 规则检索
- 历史案例回放

------

## 18. 非目标

本项目不负责：

- 替代 Java 核心业务系统
- 直接操作核心业务库
- 用大模型绕过业务规则
- 用自由文本直接驱动高风险动作
- 将所有业务都做成完全自治 Agent

------

## 19. 启动方式

### 初始化 MySQL

```bash
mysql -u root -p < sql/tao_ai_mysql_runtime.sql
```

### 安装依赖

```bash
pip install -U langchain langgraph langchain-ollama pymilvus fastapi uvicorn pydantic pymysql mcp python-dotenv prometheus-client psutil
```

### 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 查看指标

```bash
curl http://127.0.0.1:8000/metrics/
```

### 执行评估

```bash
curl -X POST http://127.0.0.1:8000/eval/run \
  -H 'Content-Type: application/json' \
  -d '{"dataset_name":"smoke","persist":true}'

curl http://127.0.0.1:8000/eval/runs
```

### 本地依赖

需要提前准备：

- Ollama
- Milvus
- MySQL
- Java MCP Server

------

## 20. 项目一句话总结

`agent-runtime` 是企业 Java 主系统之上的 Python 智能编排层。
它使用 **LangChain** 负责模型与工具抽象，使用 **LangGraph** 负责有状态多 Agent 工作流，使用 **Milvus** 负责知识与案例检索，使用 **Ollama** 负责本地模型运行，并通过 **MCP** 与 Java 业务能力连接，最终形成一个可审计、可审批、可扩展、可生产化的 Agent Runtime。
