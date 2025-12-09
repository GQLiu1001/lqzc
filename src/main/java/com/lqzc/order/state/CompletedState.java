package com.lqzc.order.state;

import com.lqzc.order.domain.OrderLifecycleState;

/**
 * @author rabbittank
 * @description 订单已完成，所有主动操作默认拒绝
 * @createDate 2025-12-10 00:00:00
 */
public class CompletedState implements OrderState {
    @Override
    public OrderLifecycleState getName() {
        return OrderLifecycleState.COMPLETED;
    }
}
