# 订单状态模式改造说明

## 改造目标
- 按订单状态拆分独立处理器，通过工厂按当前状态返回具体实现。
- 将积分发放、MQ 推送等副作用集中在状态链中，替代原有 if/else 分支。
- 便于后续扩展异常关闭、退款回滚等新场景。

## 目录结构
- `com.lqzc.order.state`
  - `OrderLifecycleState`：状态枚举。
  - `OrderState`：状态处理器接口，定义 `onEnter/next/confirm/close` 钩子。
  - `OrderContext`：上下文，持有 `OrderInfo` 及 `OrderInfoMapper`、`RabbitTemplate`、积分服务等依赖，并封装积分赠送/MQ 发送等副作用。
  - `OrderStateFactory`：根据 `orderStatus/dispatchStatus` 选择具体处理器。
  - 具体状态：
    - `WaitingDispatchState`：待派单。
    - `DispatchingState`：待接单/派送中，`next()` 进入待确认并推送加钱消息。
    - `WaitingConfirmState`：待确认，`confirm()` 完成订单并赠送积分，`onEnter` 兜底送达时间。
    - `CompletedState`：已完成（默认拒绝新操作）。
    - `ClosedState`：已关闭/取消（默认拒绝新操作）。

## 处理流程
1. 在 `OrderInfoServiceImpl` 中通过 `OrderStateFactory` 获取处理器，使用 `OrderContext` 执行动作。
   - `changeOrderDispatchStatus`：更新派送状态后调用状态处理器 `onEnter`，触发送达后的加钱消息等副作用。
   - `confirmReceive`：根据当前状态调用 `confirm`，校验状态并完成订单、赠送积分。
2. 副作用归一：
   - MQ：`OrderContext.sendAddMoneyMessage()`。
   - 积分：`OrderContext.grantCompletionPoints()`（创建账户、更新余额、写积分日志）。
3. 状态判断集中在工厂，避免散落的条件分支，扩展新状态时仅新增处理器并调整工厂映射。

## 测试
- 单元测试：`src/test/java/com/lqzc/order/state/OrderStateTest.java`
  - 验证派送中 `next()` -> 待确认，检测 MQ 推送。
  - 验证待确认 `confirm()` -> 已完成，检测积分入账与日志。
  - 已完成状态确认操作抛出异常。
- 运行：`mvn -q test`

## 扩展建议
- 退款/异常关闭：新增如 `RefundingState`，实现 `close()` 或 `next()` 处理退款回滚与消息。
- 状态流转校验：可在工厂或状态内增加版本号/乐观锁校验，避免重复操作。
- 责任链拆分副作用：如需更多副作用（库存回补、通知），可在 `OrderContext` 增加组合式处理链。 
