# TAO AI v3

> 商城 chat 和仓库 chat 都只作为前端入口，统一接入 FastAPI 的 `/chat` 接口；FastAPI 通过拦截器解析 Bearer Token，识别用户身份、id、role，并将其作为内部上下文传给 Supervisor；Supervisor 根据用户身份、角色和问题意图，将请求分发给 Mall Agent 或 Warehouse Agent；Agent 在内部按需匹配并加载对应 Skill，再决定调用 RAG、MCP Tools、外部搜索或审批流，最终由 Supervisor 汇总 `route`、`answer`、`toolCalls`、`status`，并在需要时附带 `interrupt` 后返回。
>
> **FastAPI → Supervisor（路由）→ Mall/Warehouse Agent → Skill 匹配/加载 → Tool 调用 → 返回结果 → Supervisor 汇总**。
>
> Supervisor + Warehouse subagent + Skills + interrupt_on + PostgreSQL checkpoint
>
> 项目技术栈：**LangChain v1.2.0 + LangGraph v1.1 + Deep Agents v0.5.0 + Milvus + PostgreSQL + Redis + Ollama + FastAPI**
>
> 注意 PostgreSQL、Ollama在后台 Milvus、redis 在docker
>
> 注意我会把 langchain、langgraph、deepagents 的官方 github 文件放入根目录供参考。

```yaml
version: '3.5'

services:
  etcd:
    container_name: milvus-etcd
    image: quay.io/coreos/etcd:v3.5.25
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - ./volumes/etcd:/etcd
    command: etcd -advertise-client-urls=http://etcd:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
    healthcheck:
      test: ["CMD", "etcdctl", "endpoint", "health"]
      interval: 30s
      timeout: 20s
      retries: 3

  minio:
    container_name: milvus-minio
    image: minio/minio:RELEASE.2024-05-28T17-19-04Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - ./volumes/minio:/minio_data
    command: minio server /minio_data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  standalone:
    container_name: milvus-standalone
    image: milvusdb/milvus:v2.6.13
    command: ["milvus", "run", "standalone"]
    security_opt:
      - seccomp:unconfined
    environment:
      MINIO_REGION: us-east-1
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - ./volumes/milvus:/var/lib/milvus
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/healthz"]
      interval: 30s
      start_period: 90s
      timeout: 20s
      retries: 3
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - etcd
      - minio

  attu:
    container_name: attu
    image: zilliz/attu:v2.6.3
    ports:
      - "8000:3000"
    environment:
      MILVUS_URL: standalone:19530
    depends_on:
      - standalone

networks:
  default:
    name: milvus

```

# agent 项目时序图

```mermaid
sequenceDiagram
    participant U as 用户
    participant FE as 前端页面
    participant API as FastAPI /chat
    participant INT as Auth Interceptor
    participant SUP as Supervisor
    participant MALL as Mall Agent
    participant WH as Warehouse Agent
    participant TOOL as RAG / MCP / Search / Approval

    U->>FE: 输入问题
    FE->>API: POST /chat + Authorization + message
    API->>INT: 执行拦截器
    INT->>INT: 解析 Bearer Token
    INT->>INT: 校验 token / 获取 userId / role
    INT-->>API: 注入 userContext

    API->>SUP: sessionId + message + userContext
    SUP->>SUP: 判断身份 / 角色 / 问题意图 / 路由

    alt 商城问题
        SUP->>MALL: 分发请求
        MALL->>MALL: 匹配并按需加载商城 Skill
        MALL->>TOOL: 调用 RAG / MCP / Search
        TOOL-->>MALL: 返回结果
        MALL-->>SUP: 返回候选答案 + toolCalls
    else 仓库问题
        SUP->>WH: 分发请求
        WH->>WH: 匹配并按需加载仓库 Skill
        WH->>TOOL: 调用 RAG / MCP / Search / Approval
        TOOL-->>WH: 返回结果
        WH-->>SUP: 返回候选答案 + toolCalls
    end

    SUP->>SUP: 汇总 route / answer / toolCalls / status / interrupt
    SUP-->>API: 最终结果
    API-->>FE: JSON 响应
    FE-->>U: 展示回答
```

```mermaid
sequenceDiagram
    participant SUP as Supervisor
    participant AG as Mall/Warehouse Agent
    participant TOOL as Tool / RAG / MCP / Approval

    SUP->>AG: message + userContext

    loop Reason / Act / Observe
        AG->>AG: 判断当前子目标 / 选择 Skill
        AG->>TOOL: 调用一个最合适的 Tool
        TOOL-->>AG: 返回 observation
        AG->>AG: 根据 observation 判断\n继续 / 换工具 / 补问 / 结束 / interrupt
    end

    AG-->>SUP: answer + toolCalls + status + interrupt
```



# 项目结构

```text
agent/
├── app/
│   ├── api/
│   │   ├── interrupt.py   			# 审批恢复 / decision 提交
│   │   ├── eval.py                 # /eval/offline/run, /eval/run/{id}, /eval/runs
│   │   └── chat.py                 # POST /chat
│   ├── auth/
│   │   └── auth.py         	    # Bearer Token -> userContext
│   ├── audit/						# 审计日志
│   │   ├── schemas.py
│   │   └── service.py
│   ├── core/
│   │   ├── runtime_context.py      # request-scoped user/session context
│   │   ├── config.py               # 环境变量 / 模型 / Redis / PostgreSQL 配置
│   │   ├── db.py                   # 共享异步 psycopg 连接池 (audit/eval 写入)
│   │   └── checkpoint.py           # PostgreSQL checkpointer 初始化与工厂
│   ├── schemas/
│   │   ├── agent.py                # DomainAgentResult
│   │   ├── chat.py                 # ChatRequest / ChatResponse
│   │   ├── rag.py                  # RAGSearchRequest / RAGSearchResult / RetrievedChunk
│   │   └── user.py                 # UserContext
│   ├── supervisor/
│   │   ├── state.py                # LangGraph State
│   │   ├── nodes.py                # route / mall / warehouse / finalize / fallback
│   │   ├── graph.py                # build_graph()
│   │   └── service.py              # SupervisorService.invoke()
│   ├── agents/
│   │   ├── mall_agent.py           # Mall Agent（Deep Agent）
│   │   └── warehouse_agent/      	# Warehouse Agent（Deep Agent）
│   │        ├── inventory_subagent.py
│   │        └── approval_subagent.py
│   ├── rag/
│   │   ├── service.py              # 统一 RAGService.search()
│   │   ├── ingest.py               # 文档入库 / 重建索引
│   │   ├── parser.py               # markdown / pdf / doc 文档解析
│   │   ├── chunker.py              # chunk 切分策略
│   │   ├── retriever.py            # dense / keyword / hybrid recall
│   │   ├── reranker.py             # rerank（词面 + 可选 cross-encoder）
│   │   ├── cross_reranker.py       # Qwen3-Reranker (ollama) 生成式 cross-encoder
│   │   ├── filters.py              # domain / role / tenant / warehouseScope 过滤
│   │   ├── formatter.py            # context pack / citation pack
│   │   └── constants.py
│   ├── tools/
│   │   ├── mall_tools.py
│   │   ├── warehouse_tools.py
│   │   └── rag_tools.py           # mall_rag_search / warehouse_rag_search / shared_policy
│   ├── eval/
│   │   ├── schemas.py             # EvalSample / EvalResult
│   │   ├── offline_runner.py      # 离线评测 runner
│   │   ├── online_worker.py       # 在线抽样评测 worker
│   │   ├── judges.py              # rule judge / ollama judge
│   │   └── dataset_loader.py      # JSONL golden dataset 读取
│   ├── mcp/
│   │   └── client.py               # MCP JSON-RPC over HTTP 客户端
│   └── repositories/
│       ├── redis_repo.py           # auth token 校验 (staff / customer)
│       ├── milvus_repo.py          # RAG 向量库访问
│       └── document_repo.py        # 文档元数据 / 版本 / 生效时间 / 来源登记
├── skills/
│   ├── shared/
│   │   ├── response_format/
│   │   │   └── SKILL.md
│   │   └── grounded_answer/
│   │       └── SKILL.md            # 可选：强制基于检索上下文回答
│   ├── mall/
│   │   ├── order_query/
│   │   │   ├── SKILL.md
│   │   │   └── examples.md
│   │   └── product_consult/
│   │       ├── SKILL.md
│   │       └── faq.md
│   └── warehouse/
│       ├── inventory_query/
│       │   ├── SKILL.md
│       │   └── metrics.md
│       └── outbound_approval/
│           ├── SKILL.md
│           └── rules.md
├── main.py
└── requirements.txt
```

异步边界

- API 层统一 async
- repository / rag / eval worker 尽量 async
- Deep Agent / LangGraph 若用同步 invoke，则明确在 service 层隔离
- 若主链路采用 async，则优先 `ainvoke`

“接口幂等性”说明

审批类工具、出库申请类工具，必须考虑重复提交。

- 对执行型操作支持 `idempotency_key`
- 相同 `sessionId + tool + business_key` 在短时间内重复请求时应去重

DomainAgentResult

```python
class DomainAgentResult(BaseModel):
    route: str
    answer: str
    tool_calls: list[str] = Field(default_factory=list)
    skill_used: list[str] = Field(default_factory=list)
    status: str = "success"
    interrupt: dict | None = None
    error_code: str | None = None
    error_message: str | None = None
    raw: dict | None = None
```

RetrievedChunk

```python
class RetrievedChunk(BaseModel):
    doc_id: str
    chunk_id: str
    title: str
    content: str
    score: float
    rerank_score: float | None = None
    domain: str
    scene: str | None = None
    source_type: str
    version: str | None = None
    effective_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)
```

# 0. 前端需要修改的地方

1. 增加一个仓库页面的聊天入口
2. 按照下面的接口文档实现

# 1. FastAPI 的拦截器实现

商城页面和后台页面共用 FastAPI 接口 `POST /chat` 作为统一聊天入口。前端请求统一通过 `Authorization: Bearer <token>` 传递登录态。FastAPI 在请求进入 `/chat` 前，通过拦截器解析 token，并识别当前对话用户的身份信息。

拦截器职责包括：

- 从请求头中提取 Bearer Token
- 校验 token 是否有效
- 识别当前用户类型（如 `customer / staff`）
- 解析当前用户 id 与角色信息
- 将认证结果写入请求上下文，供后续 Supervisor 使用

Java 端原有商城与后台使用不同的拦截逻辑：

- 后台通过 token 从 Redis 中获取 `userId`，再查询角色信息
- 商城通过 token 获取 `customerId`

FastAPI 端参考该逻辑重新实现，但对外统一为 `Authorization: Bearer <token>` 形式。最终目标是：**在进入 Supervisor 前，完成当前聊天用户身份、id、role 的统一解析。**

```java
// 基类拦截器
@Override
public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
    String authHeader = request.getHeader("Authorization");

    if (authHeader == null || !authHeader.startsWith("Bearer ")) {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        return false;
    }

    String token = authHeader.substring("Bearer ".length()).trim();

    if (!doAuth(token, request)) {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        return false;
    }

    return true;
}

// 后台拦截器
@Override
protected boolean doAuth(String token, HttpServletRequest request) {
    String userId = stringRedisTemplate.opsForValue().get(RedisConstant.USER_TOKEN + token);
    if (userId == null) {
        return false;
    }

    UserRole userRole = userRoleMapper.selectById(userId);
    if (userRole == null || userRole.getRoleId() == null || !this.roleValidator(userRole.getRoleId())) {
        return false;
    }

    UserContextHolder.setUserId(Long.valueOf(userId));
    UserContextHolder.setUserRoleId(userRole.getRoleId());
    UserContextHolder.setUserToken(token);
    return true;
}

// 商城拦截器（原逻辑参考）
@Override
public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
    String token = request.getHeader("X-Customer-Token");

    if (token == null || token.isEmpty()) {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write("{\"code\":401,\"message\":\"请先登录\"}");
        return false;
    }

    Long customerId = customerUserService.getCustomerIdByToken(token);
    if (customerId == null) {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write("{\"code\":401,\"message\":\"登录已过期，请重新登录\"}");
        return false;
    }

    UserContextHolder.setCustomerId(customerId);
    return true;
}
```

`UserContext` 文档化

```python
class UserContext(BaseModel):
    user_type: str                # customer / staff
    user_id: int
    role: str | None = None
    role_ids: list[int] = []
    tenant_id: str | None = None
    shop_id: str | None = None
    warehouse_scope: list[str] = []
    permissions: list[str] = []
    token: str | None = None      # 可选，通常不下传给 Agent
```

- Agent 层默认消费 `user_type / user_id / role / tenant_id / warehouse_scope`
- `token` 不应直接暴露给模型上下文
- Tools 只能消费脱敏后的运行时权限上下文

> 所有 tool 不直接暴露 `user_id / role / tenant_id` 给模型。
> 运行时身份上下文通过 `contextvars`、tool runtime wrapper 或 request-scoped service 注入。

app/core/runtime_context.py

职责：

- 保存当前请求的 `user_context`
- 保存 `session_id`
- 供 tools / repositories 在当前调用链中读取

# 2. FastAPI `/chat` 接口文档

endpoint：`POST /chat`

Authorization 请求头：

```json
{
  "Authorization": "Bearer <token>"
}
```

请求体：

- 同一个 `sessionId` 会有多轮消息
- 排查问题、做 eval、做日志关联时，光有 session 还不够，加一个 `messageId`

```json
{
  "sessionId": "chat-session-001",
  "messageId": "msg-20260417-0001",
  "message": "我想查询下我的商品"
}
```

说明：

- 前端只需要提交用户输入内容与登录 token
- `sessionId` 由前端在首次会话创建后持久化保存，并在后续多轮对话中持续透传；Supervisor 使用该值作为会话线程标识。若请求中未显式传入 `sessionId`，则由 FastAPI 服务端生成，并在响应中返回给前端；前端在后续多轮对话中需携带该 `sessionId` 继续请求
- 当前用户身份、id、role 由 FastAPI 拦截器内部解析
- `/chat` 处理器不直接处理 token，而是消费拦截器注入的用户上下文
- Supervisor 基于内部用户上下文和问题意图完成路由

成功响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "sessionId": "chat-session-001",
    "route": "mall",
    "answer": "您最近的订单为 ORD202310270001，订单状态为已完成，实付金额 3400.00 元。",
    "toolCalls": ["my_order_query"],
    "status": "success"
  }
}
{
  "code": 200,
  "message": "success",
  "data": {
    "sessionId": "chat-session-002",
    "route": "warehouse",
    "answer": "2号仓 itemId=4 当前库存为 179，最近一次出库来自订单 ORD202310270002，近7天暂无明显异常。",
    "toolCalls": ["inventory_query", "inventory_log_query"],
    "status": "success"
  }
}
{
  "code": 200,
  "message": "success",
  "data": {
    "sessionId": "chat-session-003",
    "route": "warehouse",
    "answer": "该操作需要审批人确认；确认通过后，系统才会正式提交出库审批申请。",
    "toolCalls": ["outbound_apply"],
    "status": "need_approval",
    "interrupt": {
      "id": "interrupt-warehouse-outbound-001",
      "tool": "outbound_apply",
      "args": {"warehouse_id": "2", "item_id": "4", "qty": 30, "reason": "客户急单"},
      "allowedDecisions": ["approve", "reject"]
    }
  }
}
{
  "code": 403,
  "message": "forbidden",
  "data": {
    "sessionId": "chat-session-003",
    "route": "warehouse",
    "status": "forbidden",
    "errorCode": "WAREHOUSE_ROLE_DENIED",
    "errorMessage": "当前角色无权执行仓库审批操作"
  }
}
```

# 2.1 `/chat/stream` 流式接口（SSE）

endpoint：`POST /chat/stream`

- 请求体与 `/chat` 完全一致（`sessionId / messageId / message`），鉴权同走 `Authorization: Bearer <token>`
- 响应为 `text/event-stream`，每帧 `event: <type>\ndata: <json>\n\n`
- Supervisor 内部走 `graph.astream(stream_mode=["updates","messages"])`：路由节点 LLM 的 token 会被过滤掉，只把 Mall/Warehouse Agent 生成的最终回答 token 推给前端

事件矩阵（按时间顺序）：

| event     | data                                                                | 说明                                          |
|-----------|---------------------------------------------------------------------|---------------------------------------------|
| `start`   | `{ "sessionId": "..." }`                                            | 连接建立，首次回传 sessionId（供新会话持久化）          |
| `route`   | `{ "route": "mall\|warehouse\|fallback", "reason": "..." }`         | Supervisor 三级路由给出判定                    |
| `tool`    | `{ "name": "my_order_query" }`                                      | 领域 Agent 报告的工具调用（每个工具只推一次）        |
| `delta`   | `{ "text": "您最" }`                                                  | 最终回答的 token 片段，客户端追加到消息 content         |
| `final`   | `/chat` 的完整响应体（`code / message / data`）                        | 收敛态，`answer / toolCalls / status / interrupt` 对齐同步接口 |
| `error`   | `{ "code": "INTERNAL_ERROR", "message": "..." }`                    | 流式过程中异常，随后紧跟 `done`                   |
| `done`    | `{}`                                                                | 终止标记，客户端可关闭连接                         |

```mermaid
sequenceDiagram
    participant FE as 前端
    participant API as /chat/stream
    participant SUP as Supervisor
    participant AG as Mall/Warehouse Agent

    FE->>API: POST (Authorization + body)
    API-->>FE: event:start {sessionId}
    API->>SUP: astream(state, stream_mode=[updates,messages])
    SUP->>SUP: route_node（token 不外推）
    API-->>FE: event:route {route,reason}
    SUP->>AG: domain_node
    AG-->>API: tool_calls（经 updates）
    API-->>FE: event:tool {name} * N
    AG-->>API: LLM token（经 messages）
    API-->>FE: event:delta {text} * N
    SUP->>SUP: finalize_node
    API-->>FE: event:final {code,message,data}
    API-->>FE: event:done {}
```

请求示例（curl）：

```bash
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"sessionId":"chat-session-001","messageId":"msg-001","message":"帮我查询最近的订单"}'
```

前端消费规范：

- 使用 `fetch + ReadableStream` 自行解析（`EventSource` 不支持 POST 与自定义 `Authorization`）
- 按 `delta.text` 追加到当前 AI 气泡的 `content`，收到 `final` 再用其 `answer / toolCalls / route / status / interrupt` 覆盖
- 审批分支：`final.data.status == "need_approval"` 时仍然按原方式走 `POST /chat/interrupt/decision` 恢复（审批接口保持同步）
- 音频埋点：后端会在 `event_source` 结束后统一落一条 `audit_log`（`tool_args.stream=true`），前端无需单独上报

非流式 `/chat` 接口保持向下兼容，已上线的客户端无需改动。

# 2.2 审批恢复接口

POST /chat/interrupt/decision

请求体：

```json
{
  "sessionId": "chat-session-003",
  "decision": "approve",
  "tool": "outbound_apply",
  "comment": "库存核对无误，同意出库"
}
```

- 只有有权限的审批人 admin 才能提交 `approve / reject`
- 恢复执行继续使用同一个 `thread_id=sessionId` 和 `checkpoint_ns="warehouse"`
- 恢复时沿用原发起人的运行时上下文去继续执行被中断的工具调用，不会错误切换成审批人的上下文

# 3. Supervisor 的实现

> **Supervisor 用 LangGraph 做总编排，Mall/Warehouse 用 Deep Agents 做 Agent，LangChain 负责模型与工具适配。**

```text
SupervisorService
  -> SupervisorGraph.invoke(state)
      -> route_node
          -> mall_node OR warehouse_node
              -> 调对应 Mall/WarehouseAgent
                  -> Mall/WarehouseAgent 内部按需加载 Skill
                  -> Skill 驱动调用 Tools
              -> 返回 result
      -> finalize_node
  -> 返回 ChatResponse
```

Supervisor 采用 LangGraph `StateGraph` 构建总编排流程，节点包括 `route_node`、`mall_node`、`warehouse_node`、`fallback_node`、`finalize_node`。其中 `route_node` 负责根据 `userContext + message` 判定业务域与意图，并通过条件边分发到对应 Mall/WarehouseAgent；`mall_node` 与 `warehouse_node` 分别调用 MallAgent / WarehouseAgent 执行业务推理；领域内部由 Deep Agents 负责 Skill 匹配、`SKILL.md` 读取、Tools 调用与多步任务执行；`warehouse_node` 对涉及审批的高风险工具启用 `interrupt_on` 机制；最终由 `finalize_node` 统一收敛 `route`、`answer`、`toolCalls`、`status` 并返回给 FastAPI。LangGraph 的持久化围绕 `thread_id` 工作，checkpointer 可用于多轮会话、状态恢复、审批中断恢复和排障；Deep Agents 的 human-in-the-loop 也是通过 `interrupt_on` 建在 LangGraph 的 interrupt/persistence 能力之上。

Supervisor 这一层需要解决 4 件事：

1. 接收 FastAPI 注入的 `userContext` 与用户问题
2. 基于 **身份 + 角色 + 问题意图** 做域路由
3. 调用对应的 `MallAgent` 或 `WarehouseAgent`
4. 将领域 Agent 的结果统一收敛成标准 `ChatResponse`

Supervisor 负责：

- 读取 `sessionId / message / userContext`
- 判断是 `mall` 还是 `warehouse`
- 在路由不明确时做降级或澄清
- 调用领域 Agent
- 聚合 `route / answer / toolCalls / status`
- 输出统一 JSON

Supervisor 不负责：

- 不直接查询订单、库存、审批规则
- 不直接匹配 Skill
- 不直接执行 MCP / RAG / Search
- 不维护业务规则细节

## 3.0 Checkpoint 与会话持久化设计

引入 checkpoint 的目的有 4 个：

1. 支持 `sessionId -> thread_id` 的多轮上下文连续
2. 支持审批类中断（interrupt）后的恢复执行
3. 支持节点失败后的恢复与重试
4. 支持问题排查时查看某个会话的 state / history

设计约定：

- 前端透传的 `sessionId` 作为 LangGraph 的 `thread_id`
- Supervisor、MallAgent、WarehouseAgent 共用同一个 **PostgreSQL checkpoint 后端**
- `/chat/interrupt/decision` 通过 LangGraph `Command(resume=...)` 恢复 warehouse graph
- 各图调用时统一使用 `thread_id=sessionId`
- 建议增加不同的 `checkpoint_ns`，避免 Supervisor 与领域 Agent 在同一后端中状态互相污染：
  - `supervisor`
  - `mall`
  - `warehouse`

说明：

- 同一个 `sessionId` 表示同一业务会话
- 同一个会话在不同图内执行时，共享 thread 语义，但通过 namespace 隔离状态
- 审批中断后，系统可基于 `thread_id` 恢复到上一次中断点继续执行
- 如果后续你把 Mall/Warehouse 改造成真正的 LangGraph subgraph，可进一步利用父图 checkpointer 继承能力；当前这种“Supervisor 节点里手动调用 Agent 图”的结构，仍建议显式给每个 Agent 传同一个 PostgreSQL checkpointer，并手动写 `checkpoint_ns`。

LangGraph 官方提供 `PostgresSaver` / `AsyncPostgresSaver` 作为 PostgreSQL 持久化实现；首次使用时建议执行 `.setup()` 创建所需表结构。如果你不是用 `from_conn_string()`，而是自己手动创建 psycopg 连接，则要额外注意 `autocommit=True` 与 `row_factory=dict_row`。

```python
# app/core/checkpoint.py

from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

DB_URI = (
    "postgresql://postgres:postgres@127.0.0.1:5432/agent_db"
    "?sslmode=disable"
)

@asynccontextmanager
async def create_checkpointer():
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        # 首次部署时执行一次，后续可通过 migration/init job 控制
        await checkpointer.setup()
        yield checkpointer
```

如果你想在 FastAPI 生命周期里只初始化一次，也可以这样：

```python
# main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.checkpoint import create_checkpointer

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with create_checkpointer() as checkpointer:
        app.state.checkpointer = checkpointer
        yield

app = FastAPI(lifespan=lifespan)
```

## 3.1 LangGraph State 设计

### 输入状态 `ChatInputState`

```python
class ChatInputState(TypedDict):
    session_id: str
    message: str
    user_context: dict
```

### 内部状态 `SupervisorState`

```python
class SupervisorState(TypedDict, total=False):
    session_id: str
    message: str
    user_context: dict

    route: str                     # mall / warehouse / fallback
    route_reason: str              # 命中原因，便于日志追踪
    intent: str                    # order_query / inventory_query / approval ...
    domain: str                    # mall / warehouse
    tool_calls: list[str]
    skill_used: list[str]

    agent_result: dict             # 领域 Agent 原始返回
    answer: str
    status: str                    # success / need_approval / fallback / error
    error: str | None
    interrupt: dict | None         # 审批中断信息
```

### 输出状态 `ChatOutputState`

```python
class ChatOutputState(TypedDict):
    session_id: str
    route: str
    answer: str
    tool_calls: list[str]
    status: str
    interrupt: dict | None
```

## 3.2 Graph 节点划分

### route_node

职责：

- 根据 `userContext.userType`、`role`、`message` 判断业务域
- 输出 `route / intent / route_reason`

### mall_node

职责：

- 调用 `MallAgent.invoke()`
- 接收领域结果
- 写回 `answer / tool_calls / skill_used / status`

### warehouse_node

职责：

- 调用 `WarehouseAgent.invoke()`
- 如果命中审批型工具，可能返回 `need_approval`

### fallback_node

职责：

- 处理无法识别域、越权、无权限、无命中技能等情况
- 输出兜底回复

### finalize_node

职责：

- 统一整理输出
- 清洗内部字段
- 返回标准 `ChatOutputState`

## 3.3 路由方式

`route_node` 只负责写入 `route / intent / route_reason`。
`add_conditional_edges("route", route_dispatcher, ...)` 决定跳转。LangGraph 图在 `compile()` 时接入 checkpointer；调用图时再通过 `configurable.thread_id` 绑定到具体会话线程。

```python
# app/supervisor/graph.py
from langgraph.graph import StateGraph, START, END

def build_graph(checkpointer):
    builder = StateGraph(
        SupervisorState,
        input_schema=ChatInputState,
        output_schema=ChatOutputState,
    )

    builder.add_node("route", route_node)
    builder.add_node("mall", mall_node)
    builder.add_node("warehouse", warehouse_node)
    builder.add_node("fallback", fallback_node)
    builder.add_node("finalize", finalize_node)

    builder.add_edge(START, "route")

    builder.add_conditional_edges(
        "route",
        route_dispatcher,
        {
            "mall": "mall",
            "warehouse": "warehouse",
            "fallback": "fallback",
        },
    )

    builder.add_edge("mall", "finalize")
    builder.add_edge("warehouse", "finalize")
    builder.add_edge("fallback", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile(checkpointer=checkpointer)
```

## 3.4 路由判定规则

路由不要完全靠大模型自由发挥，建议采用 **“规则优先，模型补充”**：

### 第一层：基于身份直接限流

例如：

- `customer` 默认只允许走 `mall`
- `staff` 可以走 `warehouse`
- 某些仓库审批问题必须要求 `staff + role in [warehouse_manager, admin]`

### 第二层：基于关键词 / 意图分类

例如：

- “订单、商品、退款、配送、售后” → `mall`
- “库存、入库、出库、波次、盘点、审批” → `warehouse`

### 第三层：灰区问题交给轻量意图分类器

例如：

- “帮我看下 2 号仓这个商品还能不能卖”
- “这个订单是不是已经从仓里发走了”

这类句子可以加一个轻量 LLM 分类器，输出：

```json
{
  "route": "warehouse",
  "intent": "inventory_and_outbound_status",
  "confidence": 0.84,
  "reason": "用户关注仓内库存与出库状态"
}
```

建议阈值：

- `confidence >= 0.75`：直接路由
- `0.5 ~ 0.75`：允许结合角色二次判断
- `< 0.5`：走 `fallback_node`

## 3.5 Mall / Warehouse Agent 的接入方式

把两个领域 Agent 都封装成统一接口：

```python
class DomainAgentResult(BaseModel):
    route: str
    answer: str
    tool_calls: list[str] = []
    skill_used: list[str] = []
    status: str = "success"   # success / need_approval / fallback / error
    interrupt: dict | None = None
    raw: dict | None = None

class MallAgent:
    def invoke(self, session_id: str, message: str, user_context: dict) -> DomainAgentResult:
        ...

class WarehouseAgent:
    def invoke(self, session_id: str, message: str, user_context: dict) -> DomainAgentResult:
        ...
```

## 3.6 Skill 在 Mall/WarehouseAgent 内部的工作方式

Deep Agents 的 Skill 机制可以理解为：

1. 先根据 Skill 描述判断是否匹配
2. 命中后读取对应 `SKILL.md`
3. 再按技能说明去执行，并按需读取脚本、模板、参考文档

### MallAgent 加载

- `skills/shared/response_format/`
- `skills/mall/order_query/`
- `skills/mall/product_consult/`

### WarehouseAgent 加载

- `skills/shared/response_format/`
- `skills/warehouse/inventory_query/`
- `skills/warehouse/outbound_approval/`

这样 Mall/WarehouseAgent 内部就是：

- 先读用户问题
- Deep Agent 自动匹配 Skill
- 读取对应 `SKILL.md`
- 再调用对应工具

这里有个很关键的点：**Skill 描述必须写得非常具体**，因为是否命中，首先看的是 Skill 描述本身。Deep Agents 的 Skills 属于 progressive disclosure：先看技能元信息，再在命中时展开剩余技能文件。

## 3.7 审批流接入方式

Deep Agents 官方支持 human-in-the-loop，配置方式是 `interrupt_on`。它支持：

- `True`
- `False`
- `{"allowed_decisions": [...]}`

可选 decision 包括：

- `approve`
- `edit`
- `reject`

你的仓库审批场景建议只开放：

- `approve`
- `reject`

同时，这类流程必须依赖 checkpoint 才能在 interrupt 后恢复执行，生产环境建议使用持久化后端，比如 PostgreSQL checkpointer。

```python
warehouse_agent = create_deep_agent(
    model=model,
    tools=[
        inventory_query,
        inventory_log_query,
        outbound_apply,
        approval_status_query,
    ],
    skills=[
        "skills/shared/response_format",
        "skills/warehouse/inventory_query",
        "skills/warehouse/outbound_approval",
    ],
    interrupt_on={
        "outbound_apply": {"allowed_decisions": ["approve", "reject"]},
    },
    checkpointer=checkpointer,
)
```

## 3.8 finalize_node 的职责

需要做的事：

- 兜底 `tool_calls=[]`
- 清洗空字段
- 把 `agent_result` 映射成对外响应
- 保证 `answer` 一定有值
- 对错误信息做用户友好化处理
- 对审批中断增加 `status=need_approval`

```python
def finalize_node(state: SupervisorState) -> ChatOutputState:
    answer = state.get("answer") or "抱歉，当前问题暂时无法处理，请稍后重试。"
    return {
        "session_id": state["session_id"],
        "route": state.get("route", "fallback"),
        "answer": answer,
        "tool_calls": state.get("tool_calls", []),
        "status": state.get("status", "success"),
        "interrupt": state.get("interrupt"),
    }
```

## 3.9 fallback_node

兜住这几类情况：

- 用户身份无法进入目标域
- 意图不清晰
- 领域 Agent 执行失败
- 没命中可用 Skill
- 工具超时 / 数据源异常

```python
def fallback_node(state: SupervisorState):
    return {
        "route": "fallback",
        "status": "fallback",
        "answer": "当前问题暂时无法明确归类到商城或仓库场景，请补充订单号、商品信息或仓库信息后再试。",
        "tool_calls": [],
    }
```

## 3.10 SupervisorService 调用链

1. 组装初始 state
2. 调 `graph.invoke()`
3. 把结果映射成 `ChatResponse`

这里要注意：既然已经引入 PostgreSQL checkpoint，那么 Supervisor 调用图时不要只传 `thread_id`，还应显式带上 `checkpoint_ns="supervisor"`，以便和 Mall / Warehouse Agent 隔离。LangGraph 的线程持久化配置就是通过 `configurable.thread_id` 传入。

```python
class SupervisorService:

    def __init__(self, graph):
        self.graph = graph

    def invoke(self, session_id: str, message: str, user_context: dict):
        state = {
            "session_id": session_id,
            "message": message,
            "user_context": user_context,
        }

        result = self.graph.invoke(
            state,
            config={
                "configurable": {
                    "thread_id": session_id,
                    "checkpoint_ns": "supervisor",
                }
            },
        )

        return {
            "code": 200,
            "message": "success",
            "data": {
                "sessionId": result["session_id"],
                "route": result["route"],
                "answer": result["answer"],
                "toolCalls": result["tool_calls"],
                "status": result["status"],
                "interrupt": result.get("interrupt"),
            },
        }
```

# 4. MallAgent

> **MallAgent 是商城域的领域执行器，负责处理订单、商品、售后、退款、物流等商城问题。Supervisor 只负责把请求路由到商城域；进入 MallAgent 后，由 Deep Agents 负责 Skill 匹配、工具调用和多步执行。**

MallAgent 这一层的目标，不是自己重新实现路由，而是在 **已被 Supervisor 判定为 `mall` 域** 的前提下，完成商城域内部的任务执行与结果收敛。它需要解决 5 件事：

1. 接收 `session_id / message / user_context`
2. 在商城域内部匹配合适的 Skill
3. 基于 Skill 调用订单、商品、售后、RAG 等工具
4. 将工具结果整理成用户可读答案
5. 统一返回 `DomainAgentResult` 给 Supervisor

MallAgent 负责：

- 处理商城域问题，如订单查询、商品咨询、退款售后、配送说明
- 根据用户问题触发对应商城 Skill
- 调用商城域 Tools、RAG、外部搜索
- 对工具结果做商城场景下的答案组织
- 返回统一结构给 Supervisor

MallAgent 不负责：

- 不判断是否应该走 `mall` 还是 `warehouse`
- 不负责跨域权限总控
- 不直接决定最终 HTTP 响应结构
- 不直接暴露底层数据库或 SDK 给前端

## 4.1 MallAgent 的输入输出约定

为了让 Supervisor 能稳定集成，MallAgent 对外建议继续复用统一返回模型：

```python
from pydantic import BaseModel, Field

class DomainAgentResult(BaseModel):
    route: str = "mall"
    answer: str = Field(description="面向用户的最终回复")
    tool_calls: list[str] = Field(default_factory=list, description="本轮实际调用过的工具名")
    skill_used: list[str] = Field(default_factory=list, description="本轮命中的技能名")
    status: str = Field(default="success", description="success / fallback / error / need_approval")
    interrupt: dict | None = None
    raw: dict | None = None
```

对 MallAgent 来说，输入固定为：

```python
class MallAgent:
    def invoke(self, session_id: str, message: str, user_context: dict) -> DomainAgentResult:
        ...
```

其中：

- `session_id`：与 Supervisor、LangGraph `thread_id` 对齐，保证同一会话多轮连续
- `message`：用户本轮输入
- `user_context`：FastAPI 拦截器解析出的统一身份上下文，例如 `userType / userId / role`

这里坚持一个原则：**MallAgent 只消费统一后的 `user_context`，不要再关心 token 来源到底是后台 Redis 逻辑还是商城 customer token 逻辑。**

## 4.2 MallAgent 的职责边界

MallAgent 虽然已经进入商城域，但仍然要做一次**领域内权限约束**，避免“域路由正确但数据范围越权”。

例如：

- `customer` 只能查询自己的订单、售后、收货信息
- `staff` 即使进入商城域，也只能访问其角色允许的订单或商品数据
- 商品咨询类问题可以开放给更多角色，但订单明细、退款记录必须做用户范围绑定

所以 MallAgent 内部第一步不是直接把原始问题丢给大模型，而是先做两件事：

1. **构造运行时约束**：把 `userType / userId / role / tenant / shopId` 这类信息整理成 MallAgent 可消费的上下文
2. **收敛工具可见范围**：工具层默认基于 `user_context` 做数据过滤，而不是让模型自由传任意 `customerId`

换句话说，**身份是由拦截器解析出来的，但权限真正落地要在 MallAgent 的工具调用阶段完成。**

## 4.3 MallAgent 的实现方式

MallAgent 直接封装为一个 Deep Agent 实例。`create_deep_agent()` 支持 `model`、`tools`、`skills`、`system_prompt`、`interrupt_on`、`checkpointer` 等配置；Skill 采用 progressive disclosure，命中后再展开技能文件。既然这一版已经接 PostgreSQL checkpoint，就不要再在生产文档里默认写 `MemorySaver()` 了，而应通过依赖注入把共享的 PostgreSQL checkpointer 传进来。

```python
# app/agents/mall_agent.py

from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage, SystemMessage

from app.tools.mall_tools import (
    my_order_query,
    order_detail_query,
    logistics_trace_query,
    product_consult_query,
    aftersale_policy_query,
    mall_rag_search,
)

MALL_SYSTEM_PROMPT = """
你是商城域智能助理，只处理商城相关问题。
你必须遵守以下规则：

1. 只处理商城域问题：订单、商品、售后、退款、物流、配送、发票等。
2. 不处理仓库域问题：库存、波次、出库审批、仓内作业、盘点等。
3. 涉及用户订单、售后、地址、手机号等敏感信息时，必须以当前 user_context 的身份范围为准。
4. 如果当前问题无法在商城域内解决，返回明确的降级说明，不要编造。
5. 优先复用已命中的 Skill 指引，再决定是否调用工具。
6. 回答面向终端用户时保持简洁、明确、可执行。
"""

class MallAgent:

    def __init__(self, model, checkpointer):
        self.agent = create_deep_agent(
            model=model,
            tools=[
                my_order_query,
                order_detail_query,
                logistics_trace_query,
                product_consult_query,
                aftersale_policy_query,
                mall_rag_search,
            ],
            system_prompt=MALL_SYSTEM_PROMPT,
            skills=[
                "skills/shared/response_format",
                "skills/mall/order_query",
                "skills/mall/product_consult",
            ],
            checkpointer=checkpointer,
        )

    def invoke(self, session_id: str, message: str, user_context: dict):
        runtime_guard = self._build_runtime_guard(user_context)

        result = self.agent.invoke(
            {
                "messages": [
                    SystemMessage(content=runtime_guard),
                    HumanMessage(content=message),
                ]
            },
            config={
                "configurable": {
                    "thread_id": session_id,
                    "checkpoint_ns": "mall",
                }
            },
        )

        return self._normalize_result(result, user_context=user_context)

    def _build_runtime_guard(self, user_context: dict) -> str:
        return f"""
当前请求上下文：
- domain=mall
- userType={user_context.get("userType")}
- userId={user_context.get("userId")}
- role={user_context.get("role")}

执行约束：
1. 仅处理商城域问题；
2. 涉及订单/售后/地址等敏感信息时，只能查询当前用户有权限的数据；
3. 不得要求用户再次提供系统已知身份信息；
4. 查询失败时说明原因，不要编造结果。
"""

    def _normalize_result(self, result: dict, user_context: dict) -> DomainAgentResult:
        answer = ""
        if result.get("messages"):
            answer = result["messages"][-1].content or ""

        return DomainAgentResult(
            route="mall",
            answer=answer or "抱歉，当前商城问题暂时无法处理，请稍后再试。",
            tool_calls=self._extract_tool_calls(result),
            skill_used=self._extract_skills(result),
            status="success" if answer else "fallback",
            raw=result,
        )
```

### 第一，Skill 不要写成“目录名即规则”，而要写在 `SKILL.md` 里

真正影响命中率的是 `SKILL.md` 中的描述，而不是文件夹名本身。额外脚本、FAQ、模板文件也必须在 `SKILL.md` 中被明确引用，否则 Agent 不知道它们的用途。

### 第二，MallAgent 要显式限制商城工具集

不要把仓库工具、审批工具一起塞进 MallAgent。商城域 Agent 的工具应当尽量“窄而准”，否则模型会在相似工具之间乱选，增加误调用概率。

### 第三，尽量让工具语义清晰，不让模型猜

例如工具名建议用：

- `my_order_query`
- `order_detail_query`
- `product_consult_query`
- `aftersale_policy_query`
- `logistics_trace_query`

而不是：

- `query_data`
- `search_info`
- `get_result`

## 4.4 MallAgent 的 Skill 设计

根据现在的项目目录，MallAgent 至少应挂载这几个 Skill：

```text
skills/shared/response_format/
skills/mall/order_query/
skills/mall/product_consult/
```

推荐职责如下：

### `skills/shared/response_format`

公共输出约束 Skill，负责统一回答风格，例如：

- 先给结论，再补细节
- 不输出内部表名、SQL、向量库信息
- 金额、时间、状态字段统一格式
- 数据不足时明确说明“未查询到”而不是编造

### `skills/mall/order_query`

负责订单、退款、物流、售后这类问题，例如：

- “帮我查一下最近订单”
- “这个订单退款到哪一步了”
- “为什么还没发货”
- “我买的商品什么时候到”

Skill 内要明确告诉 Agent：

- 哪些问题优先用订单工具
- 哪些字段必须走当前用户身份绑定
- 哪些情况需要组合调用多个工具，例如“订单 + 物流”
- 没有订单号时如何先做最近订单定位

### `skills/mall/product_consult`

负责商品咨询与规则型问题，例如：

- “这款商品支持七天无理由吗”
- “有没有现货”
- “这个商品适合什么人群”
- “保修多久”
- “发票怎么开”

这个 Skill 的重点不是事务查询，而是**商品资料、FAQ、售后规则、知识库检索**。

## 4.5 MallAgent 内部执行流程

MallAgent 的推荐执行链路如下：

```python
MallAgent.invoke()
  -> 组装 mall 域运行时上下文
  -> 调 Deep Agent
      -> Deep Agent 根据 prompt 命中 Skill
      -> 读取命中 Skill 的 SKILL.md 与附属文件
      -> 决定是否调用 mall_tools / RAG / Search
      -> 返回最终 messages / structured result
  -> MallAgent wrapper 归一化为 DomainAgentResult
```

这里 `thread_id=session_id` 很关键。启用 checkpointer 后，图状态会按线程保存；审批中断恢复、多轮上下文、状态查看都依赖这个 thread 绑定。

## 4.6 MallAgent 的工具层设计

`mall_tools.py` 建议不要做成“大一统工具文件”，而是做成**面向意图的窄工具**。每个工具只负责一件事，并且参数尽量由系统补全而不是让模型随便填。

例如：

```python
# app/tools/mall_tools.py

from langchain.tools import tool

@tool
def my_order_query(limit: int = 5) -> dict:
    """查询当前登录用户最近的订单列表，不允许跨用户查询。"""
    ...

@tool
def order_detail_query(order_no: str) -> dict:
    """查询当前登录用户指定订单的详情、状态、金额、支付与发货信息。"""
    ...

@tool
def logistics_trace_query(order_no: str) -> dict:
    """查询当前登录用户指定订单的物流轨迹。"""
    ...

@tool
def product_consult_query(product_id: str | None = None, question: str = "") -> dict:
    """查询商品基础信息、卖点、适用场景、售后规则等。"""
    ...

@tool
def aftersale_policy_query(question: str) -> dict:
    """查询售后、退换货、保修、发票等商城规则。"""
    ...

@tool
def mall_rag_search(query: str) -> dict:
    """从商城知识库中检索商品 FAQ、运营规则、售后说明。"""
    ...
```

这里建议注意 3 个原则：

### 1）工具内部做权限收口

不要让模型传 `customer_id`。
正确做法是工具内部从运行时上下文读取当前用户，再拼接查询条件。

### 2）工具返回结构化结果，不返回大段拼接文本

MallAgent 最终是要组织答案的，所以工具最好返回结构化字段，例如：

```python
{
  "orderNo": "ORD202310270001",
  "status": "已完成",
  "payAmount": 3400.00,
  "deliveryStatus": "已签收"
}
```

### 3）工具异常要可控

比如订单不存在、物流超时、知识库无结果，都不要直接抛裸异常给模型。应该统一为：

```python
{
  "success": False,
  "errorCode": "ORDER_NOT_FOUND",
  "message": "未查询到当前用户对应订单"
}
```

## 4.7 MallAgent 的状态收敛策略

MallAgent 最终最好只向 Supervisor 暴露 3 类状态：

```python
status in ["success", "fallback", "error"]
```

建议语义如下：

- `success`：成功回答，可能调用了一个或多个工具
- `fallback`：商城域内无法确认问题、无命中 Skill、无数据、需要补充信息
- `error`：工具异常、模型执行失败、依赖超时

## 4.8 MallAgent 与 PostgreSQL Repository 的关系

约定：

- **事务型结构化数据**：走 PostgreSQL
- **会话/缓存/token**：走 Redis
- **知识库向量检索**：走 Milvus
- **checkpoint / graph state**：走 PostgreSQL checkpointer

也就是说：

- `my_order_query / order_detail_query / logistics_trace_query` 底层默认查 PostgreSQL
- `mall_rag_search` 底层走 Milvus
- token 校验仍可走 Redis
- LangGraph 持久化状态走 PostgreSQL checkpoint

## 4.9 MallAgent 与 Supervisor 的集成方式

Supervisor 节点中不要关心 MallAgent 的内部消息历史和技能细节，只拿统一结果：

```python
def mall_node(state: SupervisorState):
    result = mall_agent.invoke(
        session_id=state["session_id"],
        message=state["message"],
        user_context=state["user_context"],
    )
    return {
        "route": "mall",
        "agent_result": result.model_dump(),
        "answer": result.answer,
        "tool_calls": result.tool_calls,
        "skill_used": result.skill_used,
        "status": result.status,
        "interrupt": result.interrupt,
    }
```

# 5. WarehouseAgent

> **WarehouseAgent 是仓储域的领域执行器，负责处理库存、出库、审批、仓储规则等问题。Supervisor 只负责把请求路由到仓储域；进入 WarehouseAgent 后，由 Deep Agents 负责仓储域内部的 Skill 匹配、subagent 委派、工具调用和审批中断处理。**

和 MallAgent 相比，WarehouseAgent 更适合优先引入 subagent。原因是仓储域天然同时包含：

- **查询类问题**：库存、库存流水、库位、出库状态
- **执行类问题**：出库申请、审批处理
- **高风险问题**：涉及仓储操作、审批流，需要 `interrupt_on`

因此，WarehouseAgent 这一层建议采用：

- **一个主 WarehouseAgent**
- **两个内部 subagent**
  - `inventory_subagent`
  - `approval_subagent`

这样做的目的不是增加复杂度，而是把**低风险查询**与**高风险执行**清晰隔离，避免所有仓储逻辑都堆进同一个 Agent 上下文里。

WarehouseAgent 需要解决 6 件事：

1. 接收 `session_id / message / user_context`
2. 在仓储域内部匹配 Skill
3. 根据问题类型决定是否委派给 `inventory_subagent` 或 `approval_subagent`
4. 基于 Skill 调用库存、审批、RAG、外部搜索等工具
5. 在需要时通过 `interrupt_on` 触发审批中断
6. 统一返回 `DomainAgentResult` 给 Supervisor

WarehouseAgent 负责：

- 处理仓储域问题，如库存、出库、审批、盘点、仓储规则
- 在仓储域内部触发对应 Skill
- 调用仓储域 Tools、RAG、审批流
- 在执行高风险工具时触发 `interrupt_on`
- 将最终结果收敛为统一结构返回给 Supervisor

WarehouseAgent 不负责：

- 不判断是否应该走 `mall` 还是 `warehouse`
- 不直接决定最终 HTTP 响应结构
- 不直接暴露底层数据库或 Redis / Milvus / PostgreSQL 给前端
- 不替代 FastAPI 做 token 解析与登录校验

## 5.1 WarehouseAgent 的输入输出约定

为了让 Supervisor 能稳定集成，WarehouseAgent 对外继续复用统一返回模型：

```python
from pydantic import BaseModel, Field

class DomainAgentResult(BaseModel):
    route: str = "warehouse"
    answer: str = Field(description="面向用户的最终回复")
    tool_calls: list[str] = Field(default_factory=list, description="本轮实际调用过的工具名")
    skill_used: list[str] = Field(default_factory=list, description="本轮命中的技能名")
    status: str = Field(default="success", description="success / need_approval / fallback / error")
    interrupt: dict | None = None
    raw: dict | None = None
```

对 WarehouseAgent 来说，输入固定为：

```python
class WarehouseAgent:
    def invoke(self, session_id: str, message: str, user_context: dict) -> DomainAgentResult:
        ...
```

其中：

- `session_id`：与 Supervisor、LangGraph `thread_id` 对齐
- `message`：用户本轮输入
- `user_context`：FastAPI 拦截器解析出的统一身份信息，例如 `userType / userId / role`

这里和 MallAgent 一样，要坚持一个原则：

**WarehouseAgent 只消费统一后的 `user_context`，不要再关心 token 到底来自后台 staff 登录还是商城 customer 登录。**

## 5.2 WarehouseAgent 的职责边界

进入 WarehouseAgent，并不代表所有仓储数据都可以直接查。
仓储域比商城域更需要强调**角色与权限约束**。

例如：

- `customer` 默认不允许直接进入仓储执行链路
- `staff` 可以查询库存、出库状态
- `warehouse_manager / admin` 才允许发起审批类动作
- 某些高风险操作即使角色合法，也要进入 `interrupt_on`

因此，WarehouseAgent 内部第一步不是直接做推理，而是先做两件事：

1. **构造仓储域运行时约束**：把 `userType / userId / role / warehouseScope` 收敛成运行时上下文
2. **收敛工具可见范围**：库存类工具与审批类工具只暴露给对应 subagent，不让模型自由乱选

换句话说：

- **身份来源**由拦截器解析
- **路由到仓储域**由 Supervisor 判定
- **仓储域内权限落地**由 WarehouseAgent 的工具层和 subagent 分工完成

## 5.3 WarehouseAgent 的实现方式

建议 WarehouseAgent 作为一个 **Deep Agent 主封装**，内部挂两个 subagent：

- `inventory_subagent`
- `approval_subagent`

为了和你现在的项目结构保持一致，建议：

- `app/agents/warehouse_agent/__init__.py`：对外暴露 `WarehouseAgent`
- `app/agents/warehouse_agent/inventory_subagent.py`：库存子代理
- `app/agents/warehouse_agent/approval_subagent.py`：审批子代理

主 WarehouseAgent 的职责是：

- 接收 Supervisor 传入的请求
- 组装仓储域运行时 guard
- 调 Deep Agent
- 归一化结果为 `DomainAgentResult`

```python
# app/agents/warehouse_agent/__init__.py

from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.warehouse_agent.inventory_subagent import build_inventory_subagent
from app.agents.warehouse_agent.approval_subagent import build_approval_subagent


WAREHOUSE_SYSTEM_PROMPT = """
你是仓储域智能助理，只处理仓储相关问题。
你必须遵守以下规则：

1. 只处理仓储域问题：库存、库位、出库、波次、审批、盘点、仓储规则等。
2. 不处理商城域问题：订单详情、商品咨询、退款售后、物流签收等。
3. 涉及库存、出库申请、审批流等问题时，必须以当前 user_context 的权限范围为准。
4. 高风险仓储操作必须通过审批机制，不得绕过 interrupt。
5. 优先复用已命中的 Skill 指引，再决定是否调用工具。
6. 如果问题不属于仓储域，明确降级，不要编造答案。
"""


class WarehouseAgent:

    def __init__(self, model, checkpointer):
        self.agent = create_deep_agent(
            model=model,
            system_prompt=WAREHOUSE_SYSTEM_PROMPT,
            subagents=[
                build_inventory_subagent(),
                build_approval_subagent(),
            ],
            skills=[
                "skills/shared/response_format",
            ],
            checkpointer=checkpointer,
        )

    def invoke(self, session_id: str, message: str, user_context: dict):
        runtime_guard = self._build_runtime_guard(user_context)

        result = self.agent.invoke(
            {
                "messages": [
                    SystemMessage(content=runtime_guard),
                    HumanMessage(content=message),
                ]
            },
            config={
                "configurable": {
                    "thread_id": session_id,
                    "checkpoint_ns": "warehouse",
                }
            },
        )

        return self._normalize_result(result)

    def _build_runtime_guard(self, user_context: dict) -> str:
        return f"""
当前请求上下文：
- domain=warehouse
- userType={user_context.get("userType")}
- userId={user_context.get("userId")}
- role={user_context.get("role")}

执行约束：
1. 仅处理仓储域问题；
2. 只允许在当前角色权限范围内查询库存、出库、审批数据；
3. 高风险操作必须通过审批，不得跳过；
4. 查询失败时说明原因，不要编造结果。
"""

    def _normalize_result(self, result: dict) -> DomainAgentResult:
        answer = ""
        if result.get("messages"):
            answer = result["messages"][-1].content or ""

        interrupt = result.get("interrupt") or result.get("__interrupt__")
        if interrupt:
            return DomainAgentResult(
                route="warehouse",
                answer="该操作需要审批人确认；确认通过后，系统才会正式提交出库审批申请。",
                tool_calls=self._extract_tool_calls(result),
                skill_used=self._extract_skills(result),
                status="need_approval",
                interrupt=interrupt,
                raw=result,
            )

        return DomainAgentResult(
            route="warehouse",
            answer=answer or "抱歉，当前仓储问题暂时无法处理，请稍后再试。",
            tool_calls=self._extract_tool_calls(result),
            skill_used=self._extract_skills(result),
            status="success" if answer else "fallback",
            raw=result,
        )
```

这里的关键点有 4 个：

1. WarehouseAgent 对 Supervisor 仍然只暴露统一 `invoke()` 接口
2. WarehouseAgent 内部才决定是否调用 subagent
3. `thread_id=session_id` 继续复用
4. `checkpoint_ns="warehouse"` 与 Supervisor、MallAgent 隔离

## 5.4 WarehouseAgent 的 subagent 设计

为了最小改动，第一版建议只拆两个 subagent。

### `inventory_subagent`

负责：

- 库存查询
- 库位信息查询
- SKU 库存明细
- 近 N 天库存流水 / 异常记录

这个 subagent 的特点是：

- 查询为主
- 风险低
- 不需要审批
- 工具集应尽量窄

```python
# app/agents/warehouse_agent/inventory_subagent.py

from app.tools.warehouse_tools import (
    inventory_query,
    inventory_log_query,
)

def build_inventory_subagent():
    return {
        "name": "warehouse_inventory_subagent",
        "description": "处理库存查询、库位查询、库存流水和库存异常分析相关问题",
        "system_prompt": """
你是仓储库存专家。
只处理库存、库位、库存日志、库存波动分析相关问题。
不要处理出库审批、仓储执行申请等高风险操作。
优先调用库存相关工具，不要编造库存数据。
""",
        "tools": [
            inventory_query,
            inventory_log_query,
        ],
        "skills": [
            "skills/shared/response_format",
            "skills/warehouse/inventory_query",
        ],
    }
```

### `approval_subagent`

负责：

- 出库申请
- 出库审批状态查询
- 高风险仓储动作
- 需要 `interrupt_on` 的执行流程

这个 subagent 的特点是：

- 执行为主
- 风险高
- 必须支持审批中断
- 只开放必要工具

```python
# app/agents/warehouse_agent/approval_subagent.py

from app.tools.warehouse_tools import (
    outbound_apply,
    approval_status_query,
)

def build_approval_subagent():
    return {
        "name": "warehouse_approval_subagent",
        "description": "处理出库申请、审批状态查询和高风险仓储动作",
        "system_prompt": """
你是仓储审批专家。
只处理出库申请、审批状态、审批流相关问题。
如果是高风险仓储动作，必须通过审批机制。
如参数不完整，应先追问，不要直接提交。
""",
        "tools": [
            outbound_apply,
            approval_status_query,
        ],
        "skills": [
            "skills/shared/response_format",
            "skills/warehouse/outbound_approval",
        ],
        "interrupt_on": {
            "outbound_apply": {"allowed_decisions": ["approve", "reject"]},
        },
    }
```

这里的思路很明确：

- **库存问题**不要暴露审批工具
- **审批问题**不要暴露库存日志之外的无关工具
- 让模型在更窄的工具集里决策，误调用率会明显更低

## 5.5 WarehouseAgent 的 Skill 设计

根据当前项目目录，WarehouseAgent 至少应挂载这几个 Skill：

```text
skills/shared/response_format/
skills/warehouse/inventory_query/
skills/warehouse/outbound_approval/
```

推荐职责如下。

### `skills/shared/response_format`

公共输出约束 Skill，负责统一仓储域回答风格，例如：

- 先给结论，再补明细
- 不输出内部表名、仓储数据库字段、SQL
- 数量、仓库编号、审批状态字段统一格式
- 无结果时明确说明“未查询到”而不是编造

### `skills/warehouse/inventory_query`

负责库存与库存日志相关问题，例如：

- “2号仓 itemId=4 还有多少库存”
- “最近 7 天这条 SKU 有没有明显波动”
- “最近一次出库是什么时候”
- “库存是不是异常减少了”

Skill 内应明确告诉 Agent：

- 哪些问题优先调用 `inventory_query`
- 哪些问题需要组合调用 `inventory_query + inventory_log_query`
- 哪些字段属于只读查询
- 查询失败时如何明确说明

### `skills/warehouse/outbound_approval`

负责审批与执行类问题，例如：

- “帮我提交这个出库申请”
- “这个审批现在到哪一步了”
- “仓库能不能直接放行这批货”
- “这个操作为什么需要审批”

Skill 内应明确告诉 Agent：

- 哪些动作属于高风险操作
- 哪些参数缺失时必须补问
- 哪些工具必须进入审批中断
- 返回结果时应如何表述“待审批 / 已拒绝 / 已通过”

## 5.6 WarehouseAgent 内部执行流程

WarehouseAgent 的推荐执行链路如下：

```text
WarehouseAgent.invoke()
  -> 组装 warehouse 域运行时上下文
  -> 调 Deep Agent
      -> Deep Agent 结合问题语义命中 Skill
      -> 判断是否委派给 inventory_subagent 或 approval_subagent
      -> 读取命中 Skill 的 SKILL.md 与附属文件
      -> 决定是否调用 warehouse_tools / RAG / Search / interrupt_on
      -> 返回最终 messages / structured result
  -> WarehouseAgent wrapper 归一化为 DomainAgentResult
```

更具体一点可以理解为：

```text
Supervisor
  -> warehouse_node
      -> WarehouseAgent.invoke()
          -> build runtime guard
          -> Deep Agent 选择 subagent
              -> inventory_subagent 或 approval_subagent
          -> 调用 Tools
          -> 如命中审批则返回 interrupt
          -> 归一化结果
      -> finalize_node
```

这里要强调一点：

**Supervisor 不需要知道是哪个 subagent 干的活。**
它只需要拿到 WarehouseAgent 统一收敛后的结果。

## 5.7 WarehouseAgent 的工具层设计

`warehouse_tools.py` 建议也像 Mall 工具层一样，采用**面向意图的窄工具**设计。

例如：

```python
# app/tools/warehouse_tools.py

from langchain.tools import tool

@tool
def inventory_query(warehouse_id: str, item_id: str) -> dict:
    """查询指定仓库下某商品当前库存。"""
    ...

@tool
def inventory_log_query(warehouse_id: str, item_id: str, days: int = 7) -> dict:
    """查询指定仓库下某商品近 N 天库存流水与出入库变化。"""
    ...

@tool
def outbound_apply(warehouse_id: str, item_id: str, qty: int, reason: str = "") -> dict:
    """提交出库申请，可能进入审批流。"""
    ...

@tool
def approval_status_query(approval_id: str) -> dict:
    """查询审批单当前状态。"""
    ...
```

这里仍然建议遵守 3 个原则。

### 1）工具内部做权限收口

不要让模型自由传角色和用户身份。
正确做法是工具内部结合 `user_context` 再做权限判断，例如：

- 当前角色是否允许发起出库申请
- 当前角色是否允许查看指定仓库数据
- 当前角色是否允许查看审批详情

### 2）工具返回结构化结果

例如：

```python
{
  "warehouseId": "WH-02",
  "itemId": "4",
  "stock": 179,
  "lastOutboundOrderNo": "ORD202310270002",
  "anomaly": False
}
```

或者：

```python
{
  "approvalId": "AP20260416001",
  "status": "pending",
  "message": "该操作已进入待审批状态"
}
```

### 3）高风险工具不要伪装成普通查询工具

例如 `outbound_apply` 就应该明确是执行型动作，而不是叫：

- `query_outbound`
- `do_task`
- `submit_data`

工具名要让模型一看就知道这东西会触发执行和审批。

## 5.8 WarehouseAgent 的审批中断策略

WarehouseAgent 和 MallAgent 最大的不同点，在于它需要稳定支持审批流。

建议原则如下：

- **低风险查询**：直接执行
- **高风险操作**：进入 `interrupt_on`
- **审批恢复**：基于同一个 `thread_id=session_id` 继续执行
- **状态返回**：统一映射为 `status="need_approval"`

例如：

```python
interrupt_on={
    "outbound_apply": {"allowed_decisions": ["approve", "reject"]}
}
```

## 5.9 WarehouseAgent 的状态收敛策略

WarehouseAgent 最终向 Supervisor 暴露 4 类状态：

```python
status in ["success", "need_approval", "fallback", "error"]
```

建议语义如下：

- `success`：成功回答，或成功完成仓储查询
- `need_approval`：命中审批中断，等待人工决策
- `fallback`：仓储域内无法明确处理、参数不足、无命中 Skill、无数据
- `error`：工具异常、模型失败、依赖超时

和 MallAgent 不同的是：

**WarehouseAgent 合理地多了一个 `need_approval`。**

因为审批中断不是错误，而是一种正常业务状态。

## 5.10 WarehouseAgent 与 PostgreSQL / Redis / Milvus 的关系

约定与 MallAgent 保持一致：

- **事务型结构化数据**：走 PostgreSQL
- **会话 / 缓存 / token**：走 Redis
- **知识库向量检索**：走 Milvus
- **checkpoint / graph state**：走 PostgreSQL checkpointer

也就是说：

- `inventory_query / inventory_log_query / approval_status_query / outbound_apply`
  底层默认查 PostgreSQL
- `warehouse_rag_search / shared_policy_rag_search` 已接入，底层走 Milvus + 本地 lexical 混合召回
- token 校验仍然由 FastAPI 拦截器 + Redis 体系负责
- Agent 图的持久化状态走 PostgreSQL checkpoint

## 5.11 WarehouseAgent 与 Supervisor 的集成方式

Supervisor 节点中不需要关心 WarehouseAgent 内部用了几个 subagent，只拿统一结果即可：

```python
def warehouse_node(state: SupervisorState):
    result = warehouse_agent.invoke(
        session_id=state["session_id"],
        message=state["message"],
        user_context=state["user_context"],
    )
    return {
        "route": "warehouse",
        "agent_result": result.model_dump(),
        "answer": result.answer,
        "tool_calls": result.tool_calls,
        "skill_used": result.skill_used,
        "status": result.status,
        "interrupt": result.interrupt,
    }
```

这点非常重要：

- `Supervisor` 继续只做域路由
- `WarehouseAgent` 自己处理域内细分执行
- `subagent` 只是 WarehouseAgent 的内部实现细节，不泄漏到上层

# 6. RAG

> **RAG 是 Mall / Warehouse 两个领域 Agent 共用的检索增强能力层，不直接挂在 Supervisor 上，也不直接暴露给前端。Supervisor 只做域路由；进入领域 Agent 后，再按需调用 RAG、MCP Tools、外部搜索或审批流。**

RAG 在这套系统里的职责，不是替代 PostgreSQL 里的结构化查询，也不是替代业务工具，而是负责处理这几类问题：

1. **规则类知识**：售后政策、仓储 SOP、审批规范、商品说明、FAQ
2. **半结构化文档**：运营手册、仓库制度、商品资料、说明文档
3. **需要引用上下文的回答**：回答必须尽量基于检索片段，而不是让模型裸答

LangChain 官方文档把 retrieval 定位成运行时获取相关上下文的能力，并进一步延伸到 RAG；同时建议把 query enhancement、retrieval validation、answer validation 作为完整链路的一部分，而不是只做“向量检索 + 拼 prompt”。

## 6.1 RAG 的职责边界

RAG 负责：

- 检索商品、商城、仓储、审批相关文档知识
- 基于 `domain / scene / role / tenant / warehouseScope` 做检索过滤
- 返回可用于生成答案的高相关片段
- 为回答提供来源片段与引用依据
- 为 eval 输出可回放的中间结果，如召回文档、rerank 后顺序、最终上下文

RAG 不负责：

- 不替代订单、库存、审批状态这类**结构化事务查询**
- 不替代 Supervisor 的域路由
- 不直接决定审批是否通过
- 不直接处理登录态与 token
- 不让模型自由跨域、跨权限检索

这里必须卡死一个原则：

**能走 PostgreSQL 精确查的，不要走 RAG。**
比如订单状态、库存数量、审批单状态，本质是事务数据，应该优先用业务工具查；RAG 更适合“规则解释、说明文档、FAQ、SOP、政策依据”这类知识增强。

## 6.2 RAG 在整体链路中的位置

推荐链路：

```text
FastAPI /chat
  -> Auth Interceptor
  -> Supervisor
      -> MallAgent / WarehouseAgent
          -> 先命中 Skill
          -> 再决定是否调用 RAG Tool
              -> RAGService.search()
                  -> query rewrite / filter / recall / rerank / context pack
              -> 返回检索上下文
          -> Agent 基于上下文生成 grounded answer
  -> Supervisor finalize
```

也就是说：

- **Supervisor 不直接碰 RAG**
- **Mall / Warehouse Agent 内部通过工具调用 RAG**
- **真正的检索逻辑收口在 `app/rag/`**

这样后面你要调：

- chunk size
- topK
- reranker
- metadata filter
- no-hit fallback
- eval

都只需要改共享 RAG 层。

## 6.3 知识源分层

你这项目建议把知识源拆成 4 层，而不是丢进一个大 Milvus collection：

> 文档入库与版本治理
>
> 文档来源：商品资料、FAQ、仓储 SOP、审批规则、共享政策
>
> 入库方式：手动导入 / 定时同步 / 后台触发
>
> 更新策略：增量更新还是全量重建
>
> 生效策略：`version / effective_at / is_active`
>
> 删除策略：逻辑失效，不立即物理删除
>
> 重建索引策略：文档大规模更新时触发 re-ingest
>
> `dev_refs` 不进入业务检索集合

### 第一层：商城知识

例如：

- 商品卖点与说明
- 售后 / 退款 / 发票 / 物流 FAQ
- 商城运营规则
- 用户可见帮助文档

### 第二层：仓储知识

例如：

- 仓储 SOP
- 出入库规范
- 审批规则
- 盘点流程
- 仓储异常处理手册

### 第三层：共享规则知识

例如：

- 平台统一政策
- 公共术语
- 通用审批说明
- 对外统一响应模板依据

### 第四层：开发参考知识（单独隔离）

你提到会把 `langchain / langgraph / deepagents` 的官方 GitHub 文件放到根目录参考。这个东西**不要混进业务 RAG 语料**。
建议单独放成 `dev_refs` 或 `framework_refs`，只给你后续做“开发助手 / 架构问答 / 内部技术检索”使用，不要让商城用户问退款时检索到 LangGraph 文档。Deep Agents 现在更适合用 SDK 方式做 subagent、skills、interrupt_on 的精细控制，官方文档里也明确提示：这些字段不是都适合靠 AGENTS.md frontmatter 配死，复杂场景要直接用 SDK。

## 6.4 检索数据设计

每个 chunk 至少建议带这些 metadata：

```json
{
  "doc_id": "WH-SOP-001",
  "chunk_id": "WH-SOP-001#03",
  "domain": "warehouse",
  "scene": "outbound_approval",
  "title": "出库审批规范",
  "source_type": "manual",
  "access_level": "staff",
  "role_allowlist": ["warehouse_manager", "admin"],
  "tenant_id": "t1",
  "warehouse_scope": ["WH-01", "WH-02"],
  "version": "2026-04-01",
  "effective_at": "2026-04-01T00:00:00",
  "is_active": true
}
```

你后面要做权限过滤、版本控制、审批规则生效时间，这些字段一个都不能少。否则模型会检索到旧版规则，或者把 customer 不该看到的仓储文档召回来。

## 6.5 检索流程设计

建议 RAG 标准流程固定成 6 步：

### 1）query normalize / rewrite

把用户原问题转成更适合检索的查询，比如补齐：

- 领域词
- SKU / 仓库号 / 订单号
- 同义词
- 规则类问题的关键词

### 2）metadata filter

先根据 `domain + user_context` 过滤，再检索：

- `customer` 不能碰 `warehouse` 内部 SOP
- `staff` 也不能默认看所有审批规则
- 只在当前 `tenant / warehouse_scope / role` 范围内检索

Milvus 官方文档支持 metadata filtering，而且过滤可以直接和 ANN 搜索结合，先缩小范围再检索。

### 3）召回

第一版建议直接做**混合召回**，不要只做 dense。

因为你这个项目里会有很多：

- 仓库编号
- 订单号
- itemId / SKU
- 审批单号
- 固定术语
- 规则条款

这类词只做语义召回很容易丢。Milvus 官方已经支持 full-text search、metadata filtering 和 hybrid / multi-vector search，所以你当前栈里第一版没必要再额外引 Elasticsearch。

推荐第一版：

- dense recall：语义召回
- keyword/full-text recall：精确术语召回
- merge 后进 rerank

当前 `tao-ai` 代码落地也按这个思路收口：

- `app/repositories/document_repo.py` 负责扫描知识源、解析文档、切 chunk、缓存 chunk 清单
- `app/repositories/milvus_repo.py` 负责建 Milvus collection、维护 metadata 字段、同步向量索引、执行 dense search
- `app/rag/retriever.py` 保留本地 lexical recall，专门兜 SKU / 仓库号 / 固定术语这类精确词
- `app/rag/service.py` 统一合并 dense + lexical 结果，再做 rerank 和 context pack

当前同步策略：

- 以 `chunk_id + checksum + version + embed_model` 生成语料签名
- 语料签名未变化时跳过重复向量化
- 语料签名变化时，重建当前 collection 再全量写入

当前 collection 至少落这些字段：

- `chunk_id / doc_id / title / content`
- `domain / scene / source_type`
- `access_level / tenant_id / role_allowlist / warehouse_scope`
- `version / effective_at_ts / is_active`
- `metadata / embedding`

### 4）rerank

先召回 20~30 个 chunk，再 rerank 到 5~8 个。
不要让 Agent 直接吃原始 top20，不然上下文噪音会很高。

当前项目提供两档 reranker，通过 `.env` 的 `RAG_RERANKER_MODE` 切换：

| 模式 | 实现 | 延迟 | 精度 |
| --- | --- | --- | --- |
| `lexical`（默认） | 纯规则：`hit.score*0.55 + overlap_ratio*0.2 + title_ratio*0.1 + bonus` | <10ms | 受限于字面 overlap，大文档 H1 变长会稀释分数 |
| `qwen` | Qwen3-Reranker（ollama 本地跑，`dengcao/Qwen3-Reranker-8B:Q3_K_M`） | 每候选 2-3s，并发 4 | 语义理解，yes/no 分桶清晰 |

#### 为什么需要 cross-encoder

词面 rerank 的两个结构性短板：

- H1 标题变长 → `title_ratio = overlap / title_tokens` 分母变大，分数被稀释
- 同主题不同角度的章节（发票红字 / 升级投诉）在字面上不含 query 核心词，`overlap_ratio` 低

大文档 + 多角度章节的语料里，词面 rerank 会给相关 chunk 打低分。cross-encoder 直接看整体语义，能识别"红字发票属于退款子流程"这种非字面关联。

#### Qwen3-Reranker 工作原理

Ollama 不暴露 token logprobs，所以采用**二元信号 + 词面分 tiebreak**：

```text
prompt: "Judge whether the Document meets the requirements based on the Query.
         Note that the answer can only be 'yes' or 'no'."
<Query>: 退款政策是怎样的？
<Document>: 商品签收后 7 日内可联系客服发起退款申请...
→ model 输出 "yes" 或 "no"
```

最终分数 = `0.7 × qwen_binary + 0.3 × lexical_rerank`：

- 模型说 yes：final ≈ 0.7-0.85（上浮到高分区）
- 模型说 no：final ≈ 0.02-0.10（压到底部被 top_k 淘汰）
- 模型超时/解析失败：降级为纯 lexical 分数，不中断检索

#### 实测对比（5 query benchmark）

| Query | Lexical | +Qwen Reranker | 提升 |
| --- | --- | --- | --- |
| 退款政策是怎样的？ | 0.251 | 0.775 | 3.1× |
| 货物破损了怎么办？ | 0.212 | 0.744 | 3.5× |
| 偏远地区运费怎么算？ | 0.338 | 0.801 | 2.4× |
| 怎么判定库存异常？ | 0.401 | 0.820 | 2.0× |
| 大批量出库谁审批？ | 0.332 | 0.858 | 2.6× |

代价：RAG 阶段耗时从 ~0.3s 涨到 4-14s（取决于候选数 × 2-3s/pair，concurrency=4）。相对于 qwen3:8b 生成的 60-80s，占比不大。

#### 相关配置

```env
RAG_RERANKER_MODE=qwen              # lexical | qwen
RAG_RERANKER_MODEL=dengcao/Qwen3-Reranker-8B:Q3_K_M
RAG_RERANKER_CONCURRENCY=4          # 并发请求 ollama 的 pair 数
RAG_RERANKER_TIMEOUT_SECONDS=15     # 单次 pair 超时
```

出问题时切回 `lexical` 即可立即回退，无需改代码。

### 5）context pack

把最终文档片段整理成统一格式，例如：

```text
[Doc#1 | score=0.92 | title=出库审批规范 | version=2026-04-01]
...
[Doc#2 | score=0.88 | title=仓储异常处理SOP | version=2026-03-15]
...
```

### 6）grounded answer

要求 Agent：

- 优先基于检索片段作答
- 片段不足时明确说“不足以确认”
- 不要把没检索到的内容当事实写出来

## 6.6 RAG 服务接口设计

建议单独做共享服务，而不是让 `mall_tools.py` 和 `warehouse_tools.py` 各写一套检索代码：

```python
class RAGSearchRequest(BaseModel):
    domain: str                  # mall / warehouse / shared
    scene: str                   # order_query / product_consult / inventory_query ...
    query: str
    top_k: int = 8
    user_context: dict
    extra_filters: dict | None = None

class RAGSearchResult(BaseModel):
    success: bool
    query: str
    rewritten_query: str | None = None
    hits: list[dict] = []
    used_filters: dict = {}
    no_hit: bool = False
```

共享服务：

```python
class RAGService:
    def search(self, req: RAGSearchRequest) -> RAGSearchResult:
        ...
```

领域工具只做薄封装：

```python
@tool
def mall_rag_search(question: str, scene: str = "general") -> dict:
    ...

@tool
def warehouse_rag_search(question: str, scene: str = "general") -> dict:
    ...
```

这样做的好处是：

- 对 Agent 来说，工具语义清晰
- 对工程来说，检索实现集中
- 对 eval 来说，统一采样与对比更容易

## 6.7 RAG 与 Mall / Warehouse Agent 的关系

MallAgent 内部更适合调用：

- `mall_rag_search`
- `shared_policy_rag_search`

场景主要是：

- 商品咨询
- 售后政策
- 发票 / 退款 / 物流说明
- 规则解释

WarehouseAgent 内部更适合调用：

- `warehouse_rag_search`
- `shared_policy_rag_search`

场景主要是：

- 仓储 SOP
- 审批规范
- 库存异常解释
- 作业流程说明

注意：

- **结构化数值类问题**优先走 PostgreSQL Tools
- **规则解释类问题**优先走 RAG
- **结构化查询 + 规则解释混合问题**允许 Tool + RAG 组合调用

例如：

- “为什么这个出库操作需要审批？”
  先用结构化工具拿到操作类型，再用 RAG 检索审批规则说明。

## 6.8 RAG 的降级策略

RAG 一定要设计 no-hit 和 low-confidence 降级，不然最容易出现“没查到还硬答”。

建议规则：

### no-hit

当召回结果为空或全部低于阈值时：

- 不直接让模型裸答
- 返回 `no_hit=True`
- Agent 给出“当前知识库未检索到足够依据”的答复
- 必要时建议补充订单号、商品名、仓库号

### low-confidence

当召回有结果，但 rerank 后最高分仍偏低时：

- 允许返回保守答案
- 必须带“不完全确定”的表述
- 不允许输出强断言

### stale-doc

若召回到旧版规则：

- 优先用 `effective_at / version / is_active` 做过滤
- 旧版本只作为参考，不进最终上下文

## 6.9 Eval 设计

你这里的 eval 不该只评“最终回答像不像”，要分成三层：

### A. 检索层指标

这是 RAG 最核心的一层，至少要有：

- `Hit@K`：正确文档是否进了前 K
- `Recall@K`：期望文档召回了多少
- `MRR`：正确文档排位是否靠前
- `NDCG@K`：相关文档整体排序质量
- `FilterPassRate`：权限 / domain / role 过滤是否正确
- `NoHitRate`：该命中的问题却没命中多少

### B. 生成层指标

至少要有：

- `AnswerCorrectness`：答案是否正确
- `Groundedness / Faithfulness`：答案是否被检索片段支撑
- `Completeness`：关键点是否答全
- `CitationPrecision`：引用片段是否真的支撑对应结论
- `RefusalPrecision`：该拒答时是否正确拒答
- `PermissionSafety`：是否泄露越权信息

### C. 运行层记录项

至少建议记录：

- `latency_ms`
- `tool_calls_count`
- `retrieved_docs_count`
- `no_hit`
- `route`
- `intent`
- `status`

LangSmith 官方评估文档现在很明确地区分了离线评估和在线评估：离线用 dataset + evaluators + experiment 做 benchmark / regression / backtest，在线则是对真实流量做自动 evaluator、采样分析和实时回放；它也支持专门评估 RAG 的中间步骤，而不是只看最终答案。

## 6.10 Eval 数据集设计

建议你自己维护 `golden set`，一条样本至少长这样：

```json
{
  "id": "wh_rag_001",
  "domain": "warehouse",
  "scene": "outbound_approval",
  "question": "为什么这批货出库前需要审批？",
  "userContext": {
    "userType": "staff",
    "userId": 1001,
    "role": "warehouse_staff"
  },
  "expected_doc_ids": ["WH-SOP-001", "WH-RULE-003"],
  "reference_answer": "该批货涉及高风险出库场景，按当前仓储审批规范需进入审批流。",
  "must_include": ["审批", "高风险"],
  "must_not_include": ["已自动通过"]
}
```

建议数据集按 4 类拆：

1. `mall_faq_golden`
2. `mall_policy_golden`
3. `warehouse_sop_golden`
4. `warehouse_approval_golden`

这样你后面做回归测试时，能清楚知道是哪一类退化了。

## 6.11 Eval 执行策略

### 6.11.1 设计目标

Eval 用于评估 RAG 与 Agent 的检索质量、回答质量、权限安全性与运行稳定性。
本项目采用**自建 eval 方案**，分为**离线 eval**与**在线 eval**两部分：

- **离线 eval**：用于开发阶段、参数调整后和版本发布前的质量回归
- **在线 eval**：用于生产环境抽样分析真实流量表现，不阻塞主请求链路

Eval 结果统一写入 PostgreSQL，供离线回归、失败样本回收和人工分析。

### 6.11.2 离线 eval

离线 eval 使用固定评测集执行回归测试。
每次发生以下变更时必须重新执行：

- chunk 策略调整
- embedding 模型替换
- rerank 策略调整
- prompt 修改
- Skill 描述或技能文件修改
- 文档源大规模更新
- 检索过滤规则修改
- 工具返回结构修改

离线评测集采用 JSONL 格式维护，按领域与场景拆分，例如：

- `mall_faq_golden.jsonl`
- `mall_policy_golden.jsonl`
- `warehouse_sop_golden.jsonl`
- `warehouse_approval_golden.jsonl`

每条评测样本至少包含：

- 问题
- 用户上下文
- 预期命中文档
- 参考答案
- 必须包含字段
- 禁止出现字段

离线 eval 至少覆盖以下指标：

#### 检索层指标

- `Hit@K`
- `Recall@K`
- `MRR`
- `NDCG@K`
- `NoHitRate`

#### 回答层指标

- `Correctness`
- `Groundedness`
- `Completeness`
- `RefusalPrecision`

#### 安全层指标

- `PermissionSafety`
- `CrossDomainLeakRate`

离线评测结果输出为：

- 指标汇总报告
- 失败样本明细
- 回归对比结果

若核心指标低于预设阈值，则该版本不得视为通过。

### 6.11.3 在线 eval

在线 eval 用于对真实请求进行抽样分析，发现检索退化、回答失真和权限异常等问题。
在线 eval 必须采用**异步评测**，不得阻塞用户请求。

执行链路如下：

```text
用户请求
  -> FastAPI /chat
  -> Supervisor / Agent / RAG
  -> 返回用户结果
  -> 异步写入 eval_queue
  -> eval worker 消费样本
  -> 规则 judge / Ollama judge 打分
  -> 写 PostgreSQL
```

在线 eval 的采样建议：

- 默认采样率 `5% ~ 10%`
- 高风险场景可提高采样率
- 审批类、越权敏感类问题建议优先抽样

在线 eval 至少记录以下字段：

- `sessionId`
- `route`
- `intent`
- `question`
- `answer`
- `toolCalls`
- `retrievedDocs`
- `noHit`
- `latencyMs`
- `status`
- `userContext`（脱敏后）
- `judgeScores`

### 6.11.4 在线 judge 设计

在线 judge 分为两类：

#### 规则 judge

用于低成本、确定性检查，例如：

- `no_hit=true` 时是否仍输出高置信度回答
- `need_approval` 时是否正确返回 `interrupt`
- 是否出现跨域回答
- 是否出现越权输出
- 是否缺失必要字段

#### Ollama judge

用于对回答质量进行模型评估，例如：

- 回答是否被检索内容支撑
- 回答是否覆盖问题关键点
- 回答是否存在明显臆造
- 回答是否与当前角色权限一致

在线 judge 只负责评分与标记，不直接影响用户本次请求结果。

### 6.11.5 失败样本回收

在线 eval 命中的失败样本必须保留，至少包括：

- 原始问题
- 最终答案
- 检索结果
- judge 评分
- route / intent / toolCalls
- 失败原因标签

失败样本用于：

- 回归测试集补充
- prompt / skill / rerank 调整
- 权限规则修正
- RAG 文档质量排查

### 6.11.6 落地组件

本项目 eval 相关组件约定如下：

- **JSONL golden dataset**：维护离线评测集，存放于 `data/eval/*.jsonl`（当前含 `mall_faq_golden.jsonl` / `mall_policy_golden.jsonl` / `warehouse_sop_golden.jsonl` / `warehouse_approval_golden.jsonl`）
- **本地 eval runner**：`app/eval/offline_runner.py` 执行离线评测与回归；`app/eval/online_worker.py` 对接 audit_log 做在线抽样
- **Ollama judge model**：`app/eval/judges.py` 含 rule_judge (must_include / must_not_include) + llm_judge (correctness / groundedness / permission_safe)
- **PostgreSQL**：`eval_run` / `eval_sample` / `online_eval_sample` 三张表存储汇总与样本明细
- **REST 入口**：`POST /eval/offline/run`、`GET /eval/run/{run_id}`、`GET /eval/runs`

## 6.12 建议的起始验收阈值

- `Hit@5 >= 0.85`
- `Recall@10 >= 0.90`
- `Groundedness >= 0.90`
- `PermissionSafety = 100%`
- `NoHitButStillAnsweredRate <= 5%`

最关键的一条不是“答得多像人”，而是：

**没依据时别乱答，越权时绝不暴露。**

## 6.13 RAG 与 Checkpoint / Interrupt 的关系

RAG 本身不是 interrupt 流，但它的上下文、检索日志、最终采用片段，最好都能跟当前会话 `thread_id=sessionId` 关联起来。
因为 LangGraph 的 persistence 是按 thread 组织 checkpoint 的，interrupt 触发时会保存状态并等待恢复，生产环境官方也明确建议用持久化 checkpointer，例如 Postgres/AsyncPostgresSaver。你这套已经上 PostgreSQL checkpoint，所以 RAG 的 trace、eval 样本、问题排查最好都跟同一个 `sessionId` 对齐。

# 7. MCP

> **MCP 在本项目中的定位，是作为 FastAPI Agent 服务访问宿主机 Java 业务能力的标准化工具协议层。当前架构中，Java 端通过 Spring AI 提供 MCP Server，FastAPI 端作为 MCP Client 按需调用。MCP 不承担路由、认证入口、会话持久化或知识检索职责，仅负责将已有 Java 业务能力以工具形式暴露给 Agent 使用。**
>
> 注意 java 端代码也在根目录，想要啥 mcp 自己写

当前项目的 MCP 设计遵循以下事实约束：

- **Java 是 MCP Server**
- **FastAPI 是 MCP Client**
- Java 端当前已通过 Spring AI 暴露若干业务工具
- FastAPI 不直接把前端请求转发给 Java，而是由 **Supervisor / MallAgent / WarehouseAgent** 在内部按需调用 MCP 工具
- 当前 MCP 主要承载的是**已有 Java 业务查询能力复用**，而不是新的 Agent 编排中心

整体调用关系如下：

```text
前端 -> FastAPI /chat -> Supervisor -> MallAgent / WarehouseAgent
                                   -> MCP Client
                                   -> Java MCP Server (/mcp)
                                   -> Java Service / Redis / DB
                                   -> 返回结构化结果
                                   -> Agent 整理答案
```

## 7.1 MCP 的职责边界

MCP 负责：

- 将 Java 端已有业务能力暴露为标准工具
- 供 MallAgent / WarehouseAgent 在内部调用
- 统一工具名称、描述、参数与返回结构
- 降低 Python 侧重复实现 Java 业务逻辑的成本
- 作为跨语言能力桥接层，承接 FastAPI 到 Java 的工具调用

MCP 不负责：

- 不负责前端接口暴露
- 不负责 Bearer Token 认证
- 不负责用户身份解析
- 不负责 Supervisor 域路由
- 不负责 RAG 检索
- 不负责 LangGraph checkpoint 持久化
- 不直接面向前端提供业务 API

因此，MCP 在本项目中是**Agent 内部工具层的一部分**，而不是系统主入口。

## 7.2 当前 MCP 架构

当前采用的是 **Spring AI MCP Server + Streamable HTTP** 方式。

Java 端配置示意：

```text
ai:
  mcp:
    server:
      enabled: true
      protocol: STREAMABLE
      streamable-http:
        mcp-endpoint: /mcp
```

说明：

- Java 服务启动后，对外暴露 MCP 端点 `/mcp`
- FastAPI 作为 Client 连接该端点
- Agent 在运行时通过 MCP Client 调用 Java 工具
- Java 工具内部继续复用现有 service、Redis、数据库查询逻辑

这一设计的核心价值在于：

1. **复用现有 Java 业务能力**
2. **避免 Python 侧重复开发相同查询逻辑**
3. **让 Agent 可以以工具选择的方式调用宿主机业务能力**

## 7.3 当前已暴露的 MCP 工具

当前 Java 端已经按业务域拆成两个原始 MCP Tool Service：

- `MallMcpTools`
- `WarehouseMcpTools`

这里有一个非常关键的实现约定：

- `customerId`
- `operatorUserId`
- `roleId`
- `idempotencyKey`

这些字段是 **FastAPI MCP adapter 内部注入的运行时参数**，不是直接暴露给模型自由填写的业务参数。也就是说，模型在 Python 侧看到的仍然应该是 `my_order_query(limit)`、`order_detail_query(order_no)`、`outbound_apply(warehouse_id, item_id, qty, reason)` 这类语义化工具；FastAPI adapter 再把当前 `user_context / sessionId / business_key` 补齐后调用 Java 原始 MCP Tool。

### Mall 侧原始 MCP Tool

#### 1）`getInventoryByModel(model)`

用途：

- 根据商品型号查询库存详情

返回：

- 型号、规格、分类、表面、仓库、库存数量、销售单价

适用场景：

- “这个型号还有库存吗”
- “TA800-01 什么价格、什么规格”
- “这个型号在哪个仓”

#### 2）`getTopSales()`

用途：

- 查询商城热销榜前五商品

返回：

- 商品型号
- 销量

适用场景：

- “最近热销商品有哪些”
- “商城卖得最好的前几款是什么”

#### 3）`searchInventory(current, size, category, surface)`

用途：

- 分页查询可售库存商品列表

返回：

- 商品列表
- 总数
- 页码
- 每页条数

适用场景：

- “现在有什么货”
- “有哪些可售瓷砖”
- “给我看某个类别的库存商品”

#### 4）`getCustomerOrders(customerId, limit=5, status=None)`

用途：

- 查询当前客户最近订单列表

返回：

- 订单号
- 订单状态与状态文案
- 应付金额
- 订单商品数
- 创建时间

适用场景：

- “我最近的订单有哪些”
- “我还有哪些待支付订单”
- “帮我看下最近 5 单”

#### 5）`getCustomerOrderDetail(customerId, orderNo)`

用途：

- 查询当前客户指定订单详情

返回：

- 订单状态
- 支付状态
- 派送状态
- 总价、优惠、应付金额、配送费
- 收货地址
- 商品明细

适用场景：

- “ORD202604170001 这单现在什么状态”
- “这笔订单用了多少积分”
- “这单买了哪些砖”

### Warehouse 侧原始 MCP Tool

#### 6）`getWarehouseInventory(warehouseNum, itemId=None, model=None)`

用途：

- 根据仓库编号和库存项 ID 或型号查询仓库库存快照

返回：

- 仓库
- itemId
- 型号、规格、分类、表面
- 当前库存
- 单箱数
- 销售价
- 更新时间

适用场景：

- “2 号仓这个 itemId 还有多少库存”
- “这个型号在 3 号仓还有没有货”

#### 7）`getInventoryLog(warehouseNum, itemId, days=7, limit=20)`

用途：

- 查询指定仓库某库存项近 N 天库存流水

返回：

- 当前库存
- 近 N 天入库/出库/调拨汇总
- 流水明细列表

适用场景：

- “2 号仓 itemId=4 最近 7 天流水”
- “这个库存最近有没有异常出库”

#### 8）`submitOutboundApply(warehouseNum, itemId, quantity, reason, operatorUserId, roleId, idempotencyKey)`

用途：

- 提交仓库出库申请并生成待审批单

返回：

- `approvalId`
- `status=pending`
- `allowedDecisions=["approve","reject"]`
- 当前库存
- 申请数量
- 申请原因

适用场景：

- “帮我申请从 2 号仓出库 30 箱”
- “这批货先提审批”

#### 9）`getApprovalStatus(approvalId)`

用途：

- 查询审批单当前状态

返回：

- 审批单号
- 当前状态
- 审批提示信息
- 申请上下文

适用场景：

- “APxxxx 现在审批到哪一步了”
- “中断恢复前先查一下审批状态”

当前 `submitOutboundApply / getApprovalStatus` 在 Java 端先通过 Redis 维护一个轻量审批状态快照，已经足够支撑：

- `interrupt_on` 的待审批返回
- `sessionId + tool + business_key` 的幂等去重
- 审批状态轮询与恢复

后续如果接入正式审批表或工作流引擎，只需要替换 Java 端存储实现，不需要改 FastAPI Agent 的工具调用层。

## 7.4 FastAPI 侧的 MCP 接入方式

MCP 相关代码收口在一个文件：

```text
app/mcp/
└── client.py
```

`app/mcp/client.py` 负责：

- 初始化 `httpx.AsyncClient`（复用连接、带全局超时）
- 封装 MCP JSON-RPC `tools/call` 请求格式
- 执行工具调用，解析 `result.content[0].text` 为结构化 JSON
- 统一错误码：`MCP_TIMEOUT / MCP_HTTP_ERROR / MCP_TOOL_ERROR / MCP_INTERNAL_ERROR`

原计划中的 `registry.py`（工具元信息缓存）与 `adapters.py`（MCP→LangChain Tool 适配）已合并到 `app/tools/mall_tools.py` 与 `app/tools/warehouse_tools.py` 内：每个 `@tool` 函数本身即是面向意图的适配器，直接调用 `mcp_client.call_tool(name, args)` 并在函数体内注入 `customerId / operatorUserId / roleId / idempotencyKey` 等运行时字段。原因是：本项目只对接一个 Java MCP Server、工具集合稳定，额外一层 registry/adapter 只会推高复杂度而收益很小。后续如需接入多个 MCP Server 或动态发现工具，再把 registry/adapters 拆出来。

## 7.5 MCP 与 Agent 的集成关系

MCP 不直接挂在 Supervisor 上，而是由领域 Agent 按需使用。

集成关系如下：

```text
Supervisor
  -> MallAgent
      -> mall tools
      -> MCP tools
      -> RAG tools
  -> WarehouseAgent
      -> warehouse tools
      -> MCP tools
      -> RAG tools
      -> approval flow
```

这里的原则是：

- **Supervisor 只做域路由**
- **MallAgent / WarehouseAgent 决定是否调用 MCP**
- **MCP 只是领域工具集的一部分**

这样设计的好处是：

1. 不破坏现有 Supervisor 边界
2. 不让路由层直接依赖 Java 工具实现
3. 保持领域内工具选择的一致性

## 7.6 MCP Tool 适配为 LangChain Tool 的方式

虽然底层能力来自 Java MCP Server，但在 Python 侧仍建议封装成语义清晰的本地工具，以便 Agent 统一使用。

例如：

```python
# app/tools/mall_tools.py

from langchain.tools import tool

@tool
async def my_order_query(limit: int = 5) -> list[dict]:
    """查询当前登录客户最近订单，不允许跨用户查询。"""
    ctx = get_runtime_user_context()
    return await mcp_client.call_tool(
        "getCustomerOrders",
        {
            "customerId": ctx.user_id,
            "limit": limit,
        },
    )

@tool
async def order_detail_query(order_no: str) -> dict:
    """查询当前登录客户某一笔订单详情。"""
    ctx = get_runtime_user_context()
    return await mcp_client.call_tool(
        "getCustomerOrderDetail",
        {
            "customerId": ctx.user_id,
            "orderNo": order_no,
        },
    )

@tool
async def get_inventory_by_model(model: str) -> dict:
    """根据商品型号查询库存、规格、价格、仓库和分类信息。"""
    return await mcp_client.call_tool("getInventoryByModel", {"model": model})

@tool
async def inventory_log_query(warehouse_id: int, item_id: int, days: int = 7) -> dict:
    """查询指定仓库某库存项近 N 天流水。"""
    return await mcp_client.call_tool(
        "getInventoryLog",
        {
            "warehouseNum": warehouse_id,
            "itemId": item_id,
            "days": days,
        },
    )

@tool
async def outbound_apply(warehouse_id: int, item_id: int, qty: int, reason: str = "") -> dict:
    """提交出库申请，必要时进入审批流。"""
    ctx = get_runtime_user_context()
    return await mcp_client.call_tool(
        "submitOutboundApply",
        {
            "warehouseNum": warehouse_id,
            "itemId": item_id,
            "quantity": qty,
            "reason": reason,
            "operatorUserId": ctx.user_id,
            "roleId": ctx.role_ids[0],
            "idempotencyKey": build_tool_idempotency_key(
                session_id=ctx.session_id,
                tool="submitOutboundApply",
                business_key=f"{warehouse_id}:{item_id}:{qty}:{reason}",
            ),
        },
    )
```

这里一定要强调：

- Java 原始 MCP Tool 可以带运行时注入字段
- Python 暴露给 Agent 的工具签名仍然要保持“面向意图”的窄接口
- `customerId / operatorUserId / roleId / idempotencyKey` 由 adapter 注入，不让模型自由填写

这样做有四个目的：

- 屏蔽底层 MCP 协议细节
- 屏蔽 Java 原始 Tool 的内部参数
- 保持 Agent 工具调用方式一致
- 保持权限与幂等逻辑由系统运行时控制
- 后续如更换 Java 接口实现，不影响 Agent 层代码

## 7.7 MCP 工具在 Mall / Warehouse 域中的使用建议

结合当前工具能力，建议如下：

### MallAgent 优先使用的 MCP 工具

- `getInventoryByModel`
- `getTopSales`
- `searchInventory`
- `getCustomerOrders`
- `getCustomerOrderDetail`

适用场景：

- 商品库存查询
- 商品列表查询
- 热销商品推荐
- 我的订单查询
- 指定订单详情查询

### WarehouseAgent 当前可直接使用的 MCP 工具

- `getWarehouseInventory`
- `getInventoryLog`
- `submitOutboundApply`
- `getApprovalStatus`
- `getInventoryByModel`

适用场景：

- 仓库库存快照查询
- 近 N 天库存流水分析
- 出库审批申请
- 审批状态轮询
- 通过型号反查库存项入口

需要额外强调两点：

1. `submitOutboundApply` 是**执行型工具**，它当前负责生成待审批单与幂等状态，不直接扣减库存。
2. 真正“审批通过后执行出库”的动作，建议继续放在后续审批恢复链路或正式工作流服务中，不要让模型在未确认审批结果时直接做扣库存。

## 7.8 MCP 的错误处理与降级策略

MCP 调用失败不能直接导致整个 `/chat` 链路崩溃，应统一处理为工具级失败，并由 Agent 做结果降级。

建议区分以下几类错误：

### 1）连接失败

例如：

- Java MCP Server 不可达
- 网络超时
- `/mcp` 端点异常

处理策略：

- 记录错误日志
- 返回工具调用失败
- Agent 给出保守答复，不编造数据

### 2）参数错误

例如：

- `model` 为空
- 分页参数非法

处理策略：

- 返回明确参数错误信息
- 允许 Agent 补问用户，而不是直接失败

### 3）权限错误

例如：

- `customer` 误调用仓库审批工具
- `roleId` 无权发起出库审批

处理策略：

- 返回明确的 `forbidden / denied` 工具错误
- Agent 走降级答复，不编造审批结果

### 4）业务无结果或状态未命中

例如：

- 型号不存在
- 审批单不存在或已过期
- 热销榜暂无数据
- 查询条件下无商品

处理策略：

- 视为正常业务结果，不应等同系统错误
- 返回“未查询到”而不是抛系统异常

### 5）服务端内部异常

例如：

- Java service 抛异常
- Redis 或数据库查询失败

处理策略：

- FastAPI 侧统一映射为工具失败
- 不把 Java 栈信息直接暴露给模型或前端

## 7.9 MCP 的审计与日志

MCP 调用应纳入统一审计与日志体系。

日志侧至少记录：

- `sessionId`
- `messageId`
- `route`
- `tool_name`
- `tool_args`（脱敏后）
- `approval_id`（如有）
- `idempotency_key`（如有）
- `latency_ms`
- `status`
- `error_code`

这样后续在以下场景下可直接排查：

- Agent 为什么没答出来
- 某个工具是不是频繁超时
- 某类问题是不是 MCP 结果为空
- 哪个 Java 工具最容易出错

## 7.10 MCP 在本项目中的落地原则

当前项目的 MCP 设计不追求“大而全”，而遵循以下原则：

1. **只接已有、稳定、明确的 Java 能力**
2. **不把 MCP 写成新的总入口**
3. **不让 Supervisor 直接依赖具体 Java 工具**
4. **领域 Agent 按需调用 MCP**
5. **工具返回必须结构化**
6. **异常必须统一收口**
7. **权限边界仍由系统运行时控制，不交给模型决定**

基于你当前实际情况，MCP 这一层的目标不是炫技，而是：

**在不破坏现有 Java 业务体系的前提下，把宿主机已有能力标准化接入 FastAPI Agent。**

---

# 12. 如何导入新文档到 RAG

这一节用于说明：新知识文档应该放在哪里、如何触发重建、如何看 trace 日志，以及如何验证新文档已经真正被检索命中。

## 12.1 文档放置位置

根据文档面向的人群和权限边界，放到以下三类目录之一：

### 1）商城客户可见文档

适用内容：

- 商品说明
- 售后政策
- 保养/清洁指南
- 面向终端客户的 FAQ

可放位置：

- `src/main/resources/manuals/`
- `tao-ai/knowledge/mall/`

说明：

- `manuals/` 更适合现有商城手册类文档
- `knowledge/mall/` 更适合后续新增的商城知识库材料
- 这些文档会进入 `domain=mall`

### 2）仓储员工可见文档

适用内容：

- 仓储 SOP
- 出入库规范
- 审批规则
- 库位、盘点、调拨相关制度

可放位置：

- `tao-ai/knowledge/warehouse/`

说明：

- 这些文档会进入 `domain=warehouse`
- 如需限制角色，可在 metadata 中配置 `role_allowlist`
- 常见允许角色包括 `staff / warehouse_manager / admin`

### 3）共享通用规则文档

适用内容：

- 跨域通用政策
- 公共术语解释
- 所有 Agent 都可复用的统一规则

可放位置：

- `tao-ai/knowledge/shared/`

说明：

- 这些文档会进入 `domain=shared`
- 适合放不属于单一商城域或仓储域的公共说明

## 12.2 支持的文件类型

当前支持的文档后缀为：

- `.md`
- `.markdown`
- `.txt`

扫描来源由 `app/rag/constants.py::default_knowledge_sources()` 统一定义。

## 12.3 scene 识别规则

`app/rag/parser.py::resolve_scene()` 当前按以下规则推断 scene：

1. 如果 source 已经显式配置了 scene，则优先使用 source 配置。
2. 如果根目录名是 `manuals`，则进一步看文件名关键词：
   - 文件名包含“售后” -> `aftersale_policy`
   - 文件名包含“保养”或“清洁” -> `product_consult`
3. 其他情况按路径第一段推断 scene。

建议：

- 售后类文档文件名尽量带“售后”
- 商品使用/保养类文档文件名尽量带“保养”或“清洁”
- 仓储规则文档按清晰目录分层，避免 scene 语义模糊

## 12.4 两种触发重建方式

### 1）CLI 重建

在 `tao-ai/` 目录下执行：

```bash
python -m app.rag.ingest
```

当前 `app/rag/ingest.py` 的 CLI 入口会调用：

```python
await ingest_default_corpus(force_refresh=True)
```

适用场景：

- 本地开发调试
- 新增文档后立即手动重建
- 观察控制台 trace 日志

### 2）REST 重建

通过管理接口触发：

```bash
curl -X POST http://localhost:8000/rag/reindex \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"forceRefresh": true}'
```

说明：

- `POST /rag/reindex` 仅允许 `user_type=staff` 且 `role=admin`
- body 同时兼容 `forceRefresh` 与 `force_refresh`
- 返回值包含 `documents / chunks / domains / milvus`

另外也可以查看当前索引摘要：

```bash
curl http://localhost:8000/rag/summary \
  -H "Authorization: Bearer <staff_or_admin_token>"
```

说明：

- `GET /rag/summary` 仅允许已登录 `staff`
- 返回当前文档数、chunk 数、domain 分布和 Milvus 可用性

## 12.5 控制台 trace 日志样例

下面是一条典型链路示例，展示从 `/chat` 进入，到路由、Agent、Tool、RAG、Milvus 再返回的日志：

```text
[TRACE]→ chat session_id="sess-abc123" user_id=1001 user_type="customer" role="customer" message="瓷砖如何退款"
[TRACE]→ supervisor.invoke session_id="sess-abc123" thread_id="sess-abc123" checkpoint_ns="supervisor"
[TRACE]→ supervisor.route_node session_id="sess-abc123" message="瓷砖如何退款" user_type="customer" role="customer"
[TRACE]← supervisor.route_node elapsed=0ms route="mall" reason="customer 身份默认走商城域" layer1="customer_only"
[TRACE]→ mall_agent.invoke session_id="sess-abc123" message="瓷砖如何退款"
[TRACE]→ tool.aftersale_policy_query session_id="sess-abc123" question="瓷砖如何退款"
[TRACE]→ tool.rag.mall_rag_search session_id="sess-abc123" query="瓷砖如何退款" scene="aftersale_policy"
[TRACE]→ rag.search session_id="sess-abc123" domain="mall" scene="aftersale_policy" query="瓷砖如何退款"
[TRACE]→ milvus._search_sync session_id="sess-abc123" query="瓷砖如何退款" top_k=8
[TRACE]← milvus._search_sync elapsed=42ms filter_expr="domain == \"mall\" and ..." dense_limit=24 raw_hits=6 hits=6
[TRACE]← rag.search elapsed=88ms rewritten_query="瓷砖 退款 售后" milvus_hits=6 lexical_hits=4 merged_hits=7 reranked_hits=3 mode="hybrid"
[TRACE]← tool.rag.mall_rag_search elapsed=89ms hits=3 no_hit=false mode="hybrid"
[TRACE]← tool.aftersale_policy_query elapsed=90ms hits=3 no_hit=false mode="hybrid"
[TRACE]← mall_agent.invoke elapsed=412ms status="success" tool_calls=["aftersale_policy_query"] skill_used=["response_format"]
[TRACE]← supervisor.invoke elapsed=420ms route="mall" status="success" tool_calls=["aftersale_policy_query"]
[TRACE]← chat elapsed=426ms route="mall" status="success" tool_calls=["aftersale_policy_query"]
```

如果是重建链路，则会看到类似日志：

```text
[TRACE]→ rag.reindex user_id=1 user_type="staff" role="admin" force_refresh=true
[TRACE]→ rag.ingest_default_corpus force_refresh=true
[TRACE]→ milvus._index_chunks_sync chunks=18 force_refresh=true
[TRACE]→ milvus._rebuild_collection collection="taoai_rag_chunks" embedding_dim=4096
[TRACE]← milvus._rebuild_collection elapsed=1794ms dropped_old=true created_new=true
[TRACE]← milvus._index_chunks_sync elapsed=34754ms available=true indexed=18 sync_skipped=false batches=1
[TRACE]← rag.ingest_default_corpus elapsed=34760ms documents=12 chunks=18
[TRACE]← rag.reindex elapsed=34761ms documents=12 chunks=18
```

## 12.6 验证步骤

新增文档后，建议按下面顺序验证：

1. 把文档放到正确目录，并确认文件后缀属于 `.md / .markdown / .txt`。
2. 执行 `python -m app.rag.ingest`，或调用 `POST /rag/reindex`。
3. 调用 `GET /rag/summary`，确认 `documents` 或 `chunks` 数量发生变化。
4. 查看控制台 trace，确认出现 `rag.ingest_default_corpus`、`milvus._index_chunks_sync`、`milvus._rebuild_collection` 或 `syncSkipped` 等日志。
5. 发起一次 `/chat`，问题内容尽量使用“只有新文档里才有”的关键词。
6. 查看 trace，确认链路中出现：
   - `tool.rag.mall_rag_search` 或 `tool.rag.warehouse_rag_search`
   - `rag.search`
   - `milvus._search_sync`
7. 如果回答仍未命中新文档，优先排查：
   - 文档是否放错 domain 目录
   - 文件名是否未命中期望的 scene 规则
   - 文档内容是否过短或关键词过弱
   - 当前用户角色是否被 `role_allowlist` 过滤

## 12.7 当前接口与实现落点

相关实现文件如下：

- `app/api/rag.py`
- `app/rag/ingest.py`
- `app/rag/service.py`
- `app/repositories/milvus_repo.py`
- `app/core/trace.py`
- `main.py`

---

# 附录 A. RAG 文档来源与索引补充说明

## A.1 当前 RAG 文档来源（已存在的）

`app/rag/constants.py::default_knowledge_sources()` 配置 7 个 source：

| source name | root 目录 | domain | access_level | 现状 |
| --- | --- | --- | --- | --- |
| `mall_manuals` | `/lqzc/src/main/resources/manuals/` | mall | customer | ✅ 有 `保养手册.txt` + `售后指南.txt` |
| `mall_skills` | `tao-ai/skills/mall/` | mall | customer | ✅ `order_query/` + `product_consult/` |
| `warehouse_skills` | `tao-ai/skills/warehouse/` | warehouse | staff（`staff/warehouse_manager/admin`） | ✅ `inventory_query/` + `outbound_approval/` |
| `shared_skills` | `tao-ai/skills/shared/` | shared | public | ✅ `grounded_answer/` + `response_format/` |
| `knowledge_mall` | `tao-ai/knowledge/mall/` | mall | customer | ✅ 已补齐首批商城知识文档（售后、商品咨询、物流、票券支付） |
| `knowledge_warehouse` | `tao-ai/knowledge/warehouse/` | warehouse | staff | ✅ 已补齐首批仓储知识文档（审批、库存规则、查询与流水） |
| `knowledge_shared` | `tao-ai/knowledge/shared/` | shared | public | ✅ 已补齐共享规范文档（权限边界、重建与发版检查） |

支持后缀：`.md` / `.markdown` / `.txt`（见 `constants.py::SUPPORTED_DOC_SUFFIXES`）。

scene 推断逻辑（`parser.py::resolve_scene`）：
- 若 source 配置了 scene 且根目录叫 `manuals`，再看文件名：含"售后" → `aftersale_policy`，含"保养/清洁" → `product_consult`
- 否则按路径第一段推断

## A.2 Milvus collection 自动创建逻辑

- **Milvus 服务进程**：**不会**自动启，用户需先启动（`docker compose up milvus`），`settings.milvus_host=localhost:19530` 能通即可
- **Collection `taoai_rag_chunks`**：**会自动创建**
  - 入口 1：`app/rag/ingest.py::ingest_default_corpus()` → `milvus_repo.index_chunks()` → `_rebuild_collection()`（drop + create + create_index）
  - 入口 2：每次 `RAGService.search` 都会 `await milvus_repo.index_chunks(...)`，靠 sha1 签名 skip 已索引的批次（`_is_collection_current`）
  - 签名状态持久化在 `tao-ai/.rag_cache/milvus_sync.json`
- **Fallback**：Milvus 连不通时 `availability()` 降级，走本地 lexical 召回，系统不崩
