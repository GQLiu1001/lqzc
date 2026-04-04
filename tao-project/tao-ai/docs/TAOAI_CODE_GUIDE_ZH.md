# TAO AI 中文代码导读

这份文档是给“没有 Python 基础、也不熟 LangChain/LangGraph”的同学看的。

你可以先记住一句最重要的话：

`tao-ai` 不是“一个大模型直接回答所有问题”，而是一个“先判断问题类型，再查资料、调工具、过审批，最后再回答”的多步骤系统。

## 1. 整体流程先看这一条线

用户发一句话进来后，主流程大致是：

1. FastAPI 接口收到请求。
2. 进入总控工作流 `SupervisorWorkflow`。
3. 总控先判断这个问题属于客服还是仓储。
4. 再判断应该走哪个 skill。
5. 进入对应子工作流。
6. 子工作流先做知识检索（RAG）。
7. 再按 skill 调业务工具。
8. 如果是高风险动作，就挂起等待人工审批。
9. 如果不需要审批，就让对应 Agent 组织最终答案。
10. 最后把答案、工具轨迹、证据、状态都写回数据库。

你可以把它想成一个流水线：

`API -> 总控分诊 -> 子流程执行 -> 审批/回答 -> 落库`

---

## 2. 入口在哪

入口文件是 [app/main.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/main.py)。

这个文件主要做三件事：

- 创建 FastAPI 应用。
- 挂载各类路由，比如 `/chat`、`/tasks`、`/files`。
- 启动日志和监控。

真正聊天入口在 [app/api/routes_chat.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/api/routes_chat.py) 的 `chat()`。

这个函数本身不复杂，它只是做转发：

- 接收前端传来的 `ChatRequest`
- 拿到运行时容器 `runtime`
- 调用 `runtime.workflow.run_chat(payload)`

所以你要找“AI 怎么开始工作的”，不要停在 API 层，要继续往 `run_chat()` 里看。

---

## 3. 总控工作流是干嘛的

核心文件是 [app/workflows/supervisor_workflow.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/workflows/supervisor_workflow.py)。

这个类最重要，因为它决定“这次请求往哪走”。

### 3.1 `WorkflowState` 是什么

这个 `TypedDict` 可以理解成：

“整个任务在系统里流转时携带的状态包”

里面会放很多字段，比如：

- `message`：用户原始问题
- `task_id`：这次请求的任务 ID
- `current_agent`：当前分给了哪个业务域
- `current_skill`：当前选中了哪个技能
- `retrieval_hits`：检索结果
- `tool_trace`：工具执行记录
- `answer`：最终回复

在 LangGraph 里，节点函数不是靠全局变量共享数据，而是靠这个 `state` 传递。

### 3.2 `_build_graph()` 是什么

这里在搭 LangGraph 状态图。

你可以把它理解成“画流程图”：

- `parse_input`
- `route_request`
- `dispatch_customer_subagent`
- `dispatch_warehouse_subagent`
- `finalize`

其中最关键的是 `add_conditional_edges(...)`：

它表示流程走到 `route_request` 后，不是固定往下走，而是要根据 `_agent_branch()` 的返回值分支。

也就是说：

- 如果判断是仓储问题，就去仓储子图
- 否则走客服子图

### 3.3 `_parse_input()` 做了什么

这一步不是回答问题，而是在“开工单”：

- 确保 session 存在
- 创建 task
- 把用户消息写进 session 历史
- 记录监控指标

为什么要这样设计？

因为在业务系统里，一次请求不仅仅要有答案，还要能追踪：

- 这是谁问的
- 属于哪个租户
- 当前执行到哪一步
- 中途调了什么工具
- 为什么失败

### 3.4 `_route_request()` 做了什么

这是“分诊”节点。

它会调用 [app/agents/supervisor/agent.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/agents/supervisor/agent.py) 里的 `route()` 方法，得到一个 `RouteDecision`。

这个决策里包含：

- 去哪个 agent
- 用哪个 skill
- 风险等级
- 是否需要审批
- 检索应该查哪个 domain
- 建议使用哪些工具

重点理解：

这里还没有真正调用大模型来“回答用户”，这里只是在决定“接下来怎么处理这个问题”。

### 3.5 `_dispatch_to_subworkflow()` 为什么存在

总控层本身不做检索、不查订单、不查库存、不生成业务答案。

它只负责把任务交给对应子流程。

所以这个函数的作用是：

- 把总控状态转换成子工作流状态
- 执行子工作流
- 把子工作流产出的结果合并回来

### 3.6 `_finalize()` 做了什么

这里是统一收尾：

- 决定最终状态
- 把 assistant 回复写入 session
- 更新 task 表
- 打日志、打指标

所以无论前面走客服还是仓储，最后都会回到这里。

---

## 4. SupervisorAgent 为什么很关键

核心文件是 [app/agents/supervisor/agent.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/agents/supervisor/agent.py)。

它的作用不是和用户聊天，而是“判断怎么派单”。

### 4.1 `route()` 的核心思想

它采用的是：

`规则优先，LLM 兜底`

也就是：

1. 先用规则判断 skill
2. 如果规则分数太低，再让 LLM 从技能列表中选一个

为什么不直接全交给大模型？

因为纯 LLM 路由有几个问题：

- 成本更高
- 可解释性更差
- 更容易漂
- 对线上稳定性不如规则稳

所以这里用的是一种很常见的工程化思路：

“能规则化的先规则化，规则覆盖不够时再交给模型补位”

### 4.2 `_route_with_llm()` 在做什么

它会把所有可选 skill 变成一个清单，让模型从里面挑一个。

注意这里不是开放式问答，而是受限分类：

- 模型只能从已有 skill 里选
- 输出必须是 JSON

这比让模型自由发挥安全很多。

### 4.3 `_try_parse_router_json()` 为什么要单独写

因为真实模型经常不老实。

就算你要求它“只输出 JSON”，它也可能输出：

- 代码块
- JSON 前加一句说明
- JSON 后再补一句解释

所以这里做了容错解析，这种写法在线上系统里非常常见。

---

## 5. Skill 是什么，不是“技能树”那种抽象概念

相关代码在：

- [app/skills/base.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/skills/base.py)
- [app/skills/registry.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/skills/registry.py)

你可以把一个 skill 理解成：

“一种可复用的问题处理模板”

例如：

- 查订单状态
- 解释退款规则
- 库存异常处理
- 补货建议

一个 skill 通常会定义：

- 它属于客服还是仓储
- 它的风险等级
- 是否需要审批
- 命中它的关键词和正则信号
- 建议查哪个知识库
- 建议调哪些工具
- 给 Agent 的额外提示词

### 5.1 `BaseSkill.evaluate()` 在做什么

它在给当前用户问题打分：

- 如果问题里有关键词，加分
- 如果命中正则，加分
- 如果上下文能说明业务域，再加分
- 如果完全没命中，但它是某个域的默认 skill，也给一点保底分

所以 skill 并不是模型“想出来”的，而是代码里明确定义的一组规则对象。

### 5.2 `SkillRegistry.select_rule_based()` 在做什么

它会遍历所有 skill，把每个 skill 都跑一遍 `evaluate()`，最后选分数最高的那个。

本质上就是一个“规则分类器”。

---

## 6. 子工作流为什么要单独抽出来

核心文件是 [app/workflows/domain_subworkflow.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/workflows/domain_subworkflow.py)。

客服和仓储看起来是两个业务域，但处理步骤其实很像：

1. 先查知识库
2. 再调业务工具
3. 过审批
4. 生成回答

所以作者抽了一个通用骨架 `DomainSubWorkflow`。

差异只放在：

- 客服子流程最后调用客服 Agent
- 仓储子流程最后调用仓储 Agent

这是一种很典型的“模板方法”式写法。

### 6.1 `_retrieve_context()` 为什么先于工具调用

因为知识库和工具解决的问题不同：

- 检索解决“规则、SOP、说明文档”
- 工具解决“实时业务数据”

例如：

- “退款规则是什么”适合检索
- “订单 A123 现在是什么状态”适合工具

先检索的好处是：

- 给模型补充业务知识
- 即使工具没查到数据，也还能尽量基于知识库回答一部分

### 6.2 `_invoke_tools()` 为什么不让模型自由调工具

这里的设计很稳：

- skill 先限定可用工具
- 再由代码决定真正执行哪些工具

这样做的优点：

- 更可控
- 更容易审计
- 不容易被 prompt 带偏
- 更适合业务系统里的安全要求

### 6.3 `_risk_gate()` 是整个项目的安全闸门

这一层很重要。

因为 AI 在业务系统里最大风险不是“答错一句话”，而是“做错一个动作”。

比如：

- 直接退款
- 直接改库存

这种动作一旦误执行，后果比普通问答错误严重得多。

所以这里采用：

`AI 先提出动作草案 -> 人工审批 -> 审批后再真正执行`

这是非常合理的企业级设计。

### 6.4 `_draft_answer()` 在做什么

它会把两类信息拼起来：

- 检索上下文
- 工具上下文

然后交给具体 Agent 生成自然语言答案。

也就是说，真正的“生成回答”是在这一步发生的，不是在路由时发生的。

---

## 7. 工具层为什么看起来这么像“后端适配器”

核心文件是 [app/tools/mcp_tools/lqzc_tools.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/tools/mcp_tools/lqzc_tools.py)。

这个类非常值得理解，因为它把“AI 系统”和“你们业务系统”接起来了。

### 7.1 `run_by_skill()` 的本质

这个方法的意思不是“随便跑工具”，而是：

“根据当前 skill，决定这次应该调哪些工具”

例如：

- 订单状态 skill 优先查订单
- 库存异常 skill 优先查库存

### 7.2 `_build_hint_queue()` 为什么有点绕

因为它要解决一个现实问题：

用户的输入是自然语言，但工具需要结构化参数。

比如用户说：

`帮我查一下 A8001 库存`

系统就得从这句话里抽出：

- 型号：`A8001`
- 意图：查库存

所以这里会：

- 提取型号
- 提取订单号
- 看有没有“库存”“发货”“物流”这类关键词
- 推断应该调哪个工具

### 7.3 为什么很多高风险工具只返回 `planned_action`

比如退款、库存调整这些工具，没有直接执行，而是返回一个草案：

- 用什么 HTTP 方法
- 调哪个接口
- 参数是什么

原因很简单：

AI 可以建议，但不能直接替你改业务数据。

所以这类工具分两步：

1. 先生成审批草案
2. 审批通过后，再由 `execute_planned_action_sync()` 真正落地

---

## 8. RAG 在这个项目里到底扮演什么角色

相关文件：

- [app/tools/rag_tools/retriever_tool.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/tools/rag_tools/retriever_tool.py)
- [app/retrieval/retriever_factory.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/retrieval/retriever_factory.py)

RAG 不是“让模型变聪明”的魔法，而是：

“在回答前，先给模型喂一份跟当前问题相关的材料”

在这个项目里，它主要用于：

- 退款政策
- 仓库 SOP
- 售后流程
- 业务说明文档

所以项目里的回答，不是单靠模型自己想，而是：

`用户问题 + 检索证据 + 工具结果 -> 生成回答`

---

## 9. 如果你现在要自己读代码，建议顺序

不要一上来就从最底层工具或数据库开始看，容易被细节淹没。

建议按这个顺序：

1. [app/api/routes_chat.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/api/routes_chat.py)
2. [app/workflows/supervisor_workflow.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/workflows/supervisor_workflow.py)
3. [app/agents/supervisor/agent.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/agents/supervisor/agent.py)
4. [app/skills/base.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/skills/base.py)
5. [app/skills/registry.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/skills/registry.py)
6. [app/workflows/domain_subworkflow.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/workflows/domain_subworkflow.py)
7. [app/tools/mcp_tools/lqzc_tools.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/tools/mcp_tools/lqzc_tools.py)
8. [app/agents/customer_service/agent.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/agents/customer_service/agent.py)
9. [app/agents/warehouse/agent.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/agents/warehouse/agent.py)

这样你会先理解“主流程”，再去看细节。

---

## 10. 你现在最容易卡住的几个点

### 10.1 LangGraph 不是什么神秘框架

先把它当成“能传状态的流程图引擎”就够了。

你现在不用一开始就掌握它全部 API，只要知道：

- `StateGraph` 是在搭流程图
- 节点函数输入输出都是 `state`
- 每个节点修改一部分状态再传给下一个节点

### 10.2 Skill 不等于模型能力

这里的 skill 更像“业务分类和处理模板”，不是模型里那种抽象技能。

### 10.3 Agent 在这个项目里也不是自主智能体

这里的 Agent 更像“带特定角色提示词的回答器”。

例如：

- 客服 Agent 负责用客服语气回答
- 仓储 Agent 负责用仓储语气回答
- Supervisor Agent 负责路由

它们不是完全自主地四处探索，而是在既定流程里承担特定职责。

---

## 11. 一句话总结整个项目

这个项目本质上是：

“一个把大模型接入业务流程的编排系统”

它不是单纯聊天机器人，而是把下面这些能力串起来：

- 路由
- 技能匹配
- RAG 检索
- 业务工具调用
- 风险审批
- 最终回答生成
- 全链路日志和状态追踪

---

## 12. 运行时装配层为什么也很重要

如果你继续往上看，会发现 [app/api/deps.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/api/deps.py) 这个文件很关键。

它不是业务逻辑文件，但它决定了：

- 模型怎么创建
- 检索器怎么创建
- 数据库封装怎么创建
- 总控工作流怎么拿到这些依赖

### 12.1 `RuntimeContainer` 是干什么的

它像一个“总装车间”。

里面把这些东西全都装起来：

- `ModelFactory`
- `MemoryStore`
- `MilvusRetriever`
- `RetrieverTool`
- `LQZCBusinessTools`
- `ApprovalTool`
- `SupervisorWorkflow`

所以以后 API 层只要拿一个 `runtime`，就等于拿到了整套运行系统。

### 12.2 `get_runtime_container()` 为什么用了缓存

因为这些对象很多都比较重：

- 模型客户端初始化有成本
- 数据库封装没必要每次请求重建
- 检索器和工作流对象也没必要每次都 new

所以这里用单例缓存非常合理。

---

## 13. 配置层怎么看才不乱

核心文件是 [app/config.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/config.py)。

你第一次看可能会觉得这个文件很长，但其实它非常规律。

它主要把配置分成几组：

- 应用配置：应用名、端口、日志、监控
- 模型配置：Ollama 地址、聊天模型、向量模型
- 数据库配置：MySQL
- 向量库配置：Milvus
- 业务工具配置：MCP、LQZC token
- AI 运行开关：是否启用审批、评测、LLM 路由
- 知识库集合配置：FAQ、政策、SOP 等 collection 名

所以这个文件你不用逐行死记，只要记住：

“凡是系统行为能调的开关，大概率都在 `Settings` 里”

### 13.1 `Settings` 为什么用 dataclass

因为它很适合做“配置对象”：

- 字段清晰
- 默认值清晰
- 初始化后就是一个普通对象，代码里访问方便

### 13.2 `__post_init__()` 在干什么

前面很多值都来自环境变量，但有些路径不是配置给的，而是可以推导出来的。

比如：

- 项目根目录
- prompts 目录
- skills 目录

所以作者把这部分放在 `__post_init__()` 里统一补齐。

---

## 14. MemoryStore、SessionMemory、TaskMemory 这三层怎么理解

相关文件：

- [app/memory/memory_store.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/memory/memory_store.py)
- [app/memory/session_memory.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/memory/session_memory.py)
- [app/memory/task_memory.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/memory/task_memory.py)
- [app/memory/mysql_store.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/memory/mysql_store.py)

这几层最容易让新手困惑，因为看起来有点“重复包装”。

其实它们分别承担不同层级的职责：

### 14.1 `MySQLStore`

这是最底层，负责直接写 SQL 和访问数据库。

你可以把它理解成：

“数据库操作员”

它关心的是：

- 建表
- 插入记录
- 更新记录
- 查询记录

### 14.2 `SessionMemory`

这是会话消息的业务封装。

它把“操作 ai_messages 表”变成了更好懂的方法：

- `append()`
- `history()`

### 14.3 `TaskMemory`

这是任务状态的业务封装。

它把“操作 ai_tasks 表”变成了：

- `create()`
- `update()`
- `get()`

### 14.4 `MemoryStore`

这是一个总入口门面。

这样上层工作流就可以写：

- `memory.session.append(...)`
- `memory.task.update(...)`
- `memory.mysql.insert_tool_trace(...)`

而不是到处传一堆分散的对象。

---

## 15. 模型层不要神化，其实就是适配层

相关文件：

- [app/models/factory.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/models/factory.py)
- [app/models/chat.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/models/chat.py)
- [app/models/embedding.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/models/embedding.py)
- [app/models/ollama_provider.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/models/ollama_provider.py)

### 15.1 `OllamaProvider`

这是最底层模型提供器。

它负责：

- 如果安装了 `langchain_ollama`，就创建 `ChatOllama` 和 `OllamaEmbeddings`
- 如果没装，也允许上层走 HTTP fallback

这说明作者在做一件很工程化的事情：

“尽量别把项目和单一依赖强耦合死”

### 15.2 `ChatService`

这个类非常重要，因为真正生成文字时，多数 Agent 最终都会走它。

它做了两件关键事：

1. 组 prompt  
   会把用户问题和上下文证据拼在一起。

2. 调模型  
   优先走 LangChain 对象；不行就直接调 Ollama HTTP 接口。

所以你可以把它理解成：

“统一的聊天模型调用入口”

### 15.3 `EmbeddingService`

它不是负责回答问题，而是负责把文本转成向量。

向量的用途是：

- 把用户问题转成向量拿去查知识库
- 把知识文档转成向量写入 Milvus

所以它是 RAG 的基础设施，不是聊天层。

### 15.4 `ModelFactory`

它负责创建这些服务对象。

作者没有在业务代码里直接 new `ChatService` / `EmbeddingService`，
而是先通过工厂来创建，这样以后要换底层 provider 时更容易集中改。

---

## 16. SkillRegistry 为什么是规则路由的中心

文件是 [app/skills/registry.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/skills/registry.py)。

它做的事可以概括成：

- 注册所有技能
- 给技能排顺序
- 输出技能目录
- 用规则挑一个最像当前问题的技能

### 16.1 `select_rule_based()` 是怎么选的

你可以把它理解成一场“候选人打分赛”：

1. 每个 skill 先自己算一个原始分数
2. 如果系统先猜到这是仓储域，就给仓储技能再加点分
3. 如果分数太低且不是默认技能，就直接淘汰
4. 最后选分数最高的那个

### 16.2 `_infer_domain_hint()` 有什么价值

它不是最终路由结果，而是一个“粗粒度预判”。

比如看到“库存、补货、锁库”，就偏向仓储；
看到“订单、物流、退款、工单”，就偏向客服。

这会让后续的 skill 评分更符合业务直觉。

---

## 17. 审批层为什么要单独抽一个工具

文件是 [app/tools/approval_tools/approval_tool.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/tools/approval_tools/approval_tool.py)。

它的作用很简单，但非常必要：

- 发起审批请求
- 记录审批通过/拒绝
- 查询审批状态

你可能会问：既然审批最后还是写数据库，为什么不直接在工作流里写 SQL？

原因是把“审批逻辑”抽出来以后：

- 工作流更干净
- 审批表结构怎么变，影响面更小
- 后面如果审批流复杂化，更容易扩展

如果你愿意，我下一步可以继续帮你做两件很实用的事：

1. 再给你单独写一份“从 `/chat` 请求开始逐行讲解”的文件级导读。
2. 继续把 [supervisor_workflow.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/workflows/supervisor_workflow.py) 和 [domain_subworkflow.py](/Users/rabbittank1001/IdeaProjects/lqzc/tao-project/tao-ai/app/workflows/domain_subworkflow.py) 做成更细的“逐函数白话版”。  
