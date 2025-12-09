package com.lqzc.order.state;

import com.lqzc.common.constant.DispatchConstant;
import com.lqzc.common.domain.OrderInfo;
import com.lqzc.order.OrderContext;
import com.lqzc.order.domain.OrderLifecycleState;

/**
 * @author rabbittank
 * @description 订单处于“待接单/派送中”状态，下一步进入待确认
 * @createDate 2025-12-10 00:00:00
 */
public class DispatchingState implements OrderState {
    @Override
    public OrderLifecycleState getName() {
        return OrderLifecycleState.DISPATCHING;
    }

    @Override
    public void next(OrderContext context) {
        OrderInfo orderInfo = context.getOrderInfo();
        orderInfo.setDispatchStatus(DispatchConstant.FINISH_DISPATCH);
        orderInfo.setOrderStatus(3);
        if (orderInfo.getReceiveTime() == null) {
            orderInfo.setReceiveTime(context.now());
        }
        context.saveOrder();
        context.sendAddMoneyMessage();
    }
}
