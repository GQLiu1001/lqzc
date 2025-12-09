package com.lqzc.order.state;

import com.lqzc.common.constant.DispatchConstant;
import com.lqzc.common.domain.OrderInfo;
import com.lqzc.order.OrderContext;
import com.lqzc.order.domain.OrderLifecycleState;

/**
 * @author rabbittank
 * @description 订单处于“待派单/待发货”状态
 * @createDate 2025-12-10 00:00:00
 */
public class WaitingDispatchState implements OrderState {
    @Override
    public OrderLifecycleState getName() {
        return OrderLifecycleState.WAITING_DISPATCH;
    }

    @Override
    public void next(OrderContext context) {
        OrderInfo orderInfo = context.getOrderInfo();
        orderInfo.setDispatchStatus(DispatchConstant.WAITING_DRIVER);
        context.saveOrder();
    }
}
