---
name: outbound_approval
description: 处理出库申请提交、审批状态查询和高风险仓储动作，出库申请会触发审批中断等待人工决策
---

# 出库审批技能

## 适用问题
- "帮我提交这个出库申请"
- "这个审批现在到哪一步了"
- "仓库能不能直接放行这批货"
- "这个操作为什么需要审批"
- "AP20260416001 审批通过了吗"

## 工具使用指引

### 提交出库申请
调用 `outbound_apply(warehouse_id, item_id, qty, reason)`:
- **必须参数**: warehouse_id, item_id, qty
- **缺少任何一个参数都应追问用户**，不要用默认值凑
- 此工具会触发审批中断（interrupt_on），系统进入待审批状态
- 只有 admin 或 warehouse_manager 角色可以发起

### 查审批状态
调用 `approval_status_query(approval_id)`:
- 返回 pending（待审批）/ approved（已通过）/ rejected（已拒绝）
- 不需要特殊权限即可查询

### 审批规则解释
如果用户问"为什么需要审批"，使用 warehouse_rag_search 检索审批规范文档。

## 高风险操作标识
以下操作属于高风险，必须进入审批流：
- 出库申请（outbound_apply）
- 后续可能新增的：调拨申请、强制冲正等

## 权限约束
- 只有 admin / warehouse_manager / staff 可以发起出库申请
- customer 角色不允许触达此技能
- 审批通过/拒绝只能由 admin 通过 `/chat/interrupt/decision` 接口操作

## 回答格式
- 审批提交后告知审批单号和当前状态
- 审批状态使用中文（待审批/已通过/已拒绝）
- 如有审批理由或驳回原因，一并输出

参考审批规则见 [rules.md](rules.md)
