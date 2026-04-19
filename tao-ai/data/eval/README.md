# Eval Datasets

`data/eval/` 存放 TAO AI 的离线 golden dataset，供 `POST /eval/offline/run` 或 `python -m app.eval.offline_runner` 使用。

当前包含 4 组数据集：

- `mall_faq_golden.jsonl`：商城 FAQ、售后与物流常见问答
- `mall_policy_golden.jsonl`：商城规则、发票、支付与地址修改政策
- `warehouse_sop_golden.jsonl`：仓储查询、库存规则与 SOP 问答
- `warehouse_approval_golden.jsonl`：审批参数、角色权限、幂等与拒绝处理

每条样本至少包含以下字段：

- `id`
- `domain`
- `scene`
- `question`
- `user_context`
- `expected_doc_ids`
- `reference_answer`
- `must_include`
- `must_not_include`

维护约定：

- 新增知识文档后，优先补充对应 `expected_doc_ids`
- 改动 Skill、Prompt、过滤规则、检索策略后，至少回归 4 组数据集
- 若新增业务域场景，按同样命名规则补充新的 `*_golden.jsonl`
