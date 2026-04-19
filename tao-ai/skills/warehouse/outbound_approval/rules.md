# 出库审批规则

## 审批触发条件
- 所有通过 Agent 发起的出库申请均需审批
- 超权限出库（超出角色日限额）必须审批
- 涉及危险品需二级审批

## 审批流程
1. staff / warehouse_manager 通过 Agent 提交出库申请
2. 系统生成审批单号（AP + 时间戳 + 随机码）
3. 系统进入待审批状态（interrupt），暂停执行
4. admin 通过 `/chat/interrupt/decision` 接口提交 approve / reject
5. 系统恢复执行：
   - approve → 执行出库扣减库存
   - reject → 取消申请并通知申请人

## 审批角色
- **申请人**: staff, warehouse_manager
- **审批人**: admin（仅 admin 可 approve/reject）
- **查询人**: 所有仓储角色均可查询审批状态

## 幂等性
- 相同 sessionId + tool + warehouse_id + item_id 在短时间内重复请求应去重
- 使用 idempotency_key 防止重复提交

## 超时处理
- 审批单超过 24 小时未处理，标记为过期
- 过期审批单不自动通过，需重新提交
