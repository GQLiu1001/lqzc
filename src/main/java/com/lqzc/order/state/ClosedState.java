package com.lqzc.order.state;

import com.lqzc.order.domain.OrderLifecycleState;

/**
 * @author rabbittank
 * @description 订单已关闭/取消，所有操作直接拒绝
 * @createDate 2025-12-10 00:00:00
 */
public class ClosedState implements OrderState {
    @Override
    public OrderLifecycleState getName() {
        return OrderLifecycleState.CLOSED;
    }
}
