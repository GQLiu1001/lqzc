# Tao AI Runtime TODO

更新时间: 2026-04-01

## 当前阶段
目标：在已完成 `skill + subagent + tool 闭环第一版` 的基础上，补齐“生产可执行闭环”。

## README 对齐差距（企业级视角）
- [x] 技术栈迁移：LangChain + LangGraph + Milvus + MySQL + Redis
- [x] Skill 分层与子工作流拆分（客服 / 仓储）
- [x] Prometheus 基础指标暴露（含 stuck/loop/memory）
- [x] Eval 回放闭环（可运行、可落库、可查询）
- [ ] 审批后真实执行闭环（现在仍以 draft 为主）
- [ ] 工作流持久恢复（checkpointer + crash recover）
- [ ] 任务详情完整可观测（timeline + traces 完整返回）
- [ ] 统一错误码与补救策略（Tool/RAG/Model 全链路）
- [ ] 测试基线与 CI 稳定门禁

## P0（本周必须完成）
### 1) Tool 闭环第二阶段：审批后真实执行
- [x] 设计并实现 `action_executor`（含幂等键与审计上下文）
- [x] `submit_refund_for_approval`：approve 后真正调用执行端
- [x] `submit_inventory_adjustment_for_approval`：approve 后真正调用执行端
- [x] `/tasks/approve`：
  - [x] `approve`：执行动作 + 回写结果
  - [x] `reject`：仅写审计，不触发副作用
  - [x] `edit_and_approve`：按 approve 路径执行
- [x] 回写一致性：
  - [x] `ai_tool_traces` 记录 action request/response/error
  - [x] `ai_tasks.final_response` 合并最终执行结论
  - [x] `approval_trace` 明确“谁在何时审批了什么”

### 2) Tool 失败治理（用户可感知）
- [ ] 建立统一错误码：`FAILED_INPUT/FAILED_CONFIG/FAILED/TIMEOUT/UPSTREAM_5XX`
- [ ] 为每类错误输出“可执行补救建议”（缺 token、参数不全、上游故障）
- [ ] API 响应中保留 `tool_events[].status/code/message/recovery_hint`

### 3) 任务查询闭环
- [ ] 完成 `GET /tasks/{task_id}` 返回：
  - [ ] `tool_trace`
  - [ ] `retrieval_trace`
  - [ ] `approval_trace`
  - [ ] `timeline`（状态流转时间线）
- [ ] 增加 `WAITING_APPROVAL -> EXECUTING_APPROVED_ACTION -> COMPLETED/FAILED` 显式状态

## P1（下阶段）
### 4) 持久恢复与稳定性
- [ ] Supervisor/Domain graph 接入持久化 checkpointer（MySQL/Redis）
- [ ] 支持 `resume/retry`（进程重启后可恢复任务）
- [ ] 长任务心跳与超时中断策略（避免假死）

### 5) 模型层生产化
- [ ] Chat/Embedding 统一重试和超时策略
- [ ] Embedding 模型可配置且启动自检（避免 `model not found`）
- [ ] 主备降级策略（主模型失败切备用模型）
- [ ] token、耗时、错误率指标统一打点

### 6) RAG 质量提升
- [ ] query rewrite（短问句补全业务上下文）
- [ ] metadata filter 策略化（tenant/doc_type/risk_level）
- [ ] rerank（多特征融合）
- [ ] 上传切片与向量维度一致性校验（防止 dim mismatch）

## P2（质量与工程化）
### 7) 测试与门禁
- [ ] unit：router/skills/tools/schemas
- [ ] integration：MCP + MySQL + Redis + Milvus + Ollama
- [ ] workflow：risk gate / approval gate / recovery gate
- [ ] eval regression：smoke + customer + warehouse 基线
- [ ] CI 门禁：核心链路失败即阻断合并

### 8) 可观测性看板与告警
- [ ] Grafana dashboard（吞吐、失败率、延迟、stuck、loop、内存、GC）
- [ ] 告警规则：
  - [ ] stuck 任务持续 > 阈值
  - [ ] loop suspect 连续增长
  - [ ] tool 失败率超阈值
  - [ ] event loop lag 异常

## 验收标准（DoD）
- [ ] 高风险请求 100% 进入审批
- [ ] 审批通过后真实动作可执行、可幂等、可审计
- [ ] `/chat` 95% 请求返回结构化 `tool_events`
- [ ] `/tasks/{task_id}` 可完整追踪执行证据链
- [ ] `/eval/run` 稳定跑完 smoke 全量并可查历史
- [ ] CI 中至少 20 条自动化测试稳定通过

## 本周执行顺序（建议）
1. `action_executor` + `/tasks/approve` 真实执行闭环
2. `GET /tasks/{task_id}` trace/timeline 补齐
3. 统一错误码与 recovery hint
4. 第一批集成测试 + Grafana 告警规则
