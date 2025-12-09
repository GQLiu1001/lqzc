package com.lqzc.order.state;

import com.lqzc.common.domain.OrderInfo;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.order.OrderContext;
import com.lqzc.order.domain.OrderLifecycleState;

/**
 * @author rabbittank
 * @description 订单已送达，等待客户确认收货
 * @createDate 2025-12-10 00:00:00
 */
public class WaitingConfirmState implements OrderState {
    @Override
    public OrderLifecycleState getName() {
        return OrderLifecycleState.WAITING_CONFIRM;
    }

    @Override
    public void onEnter(OrderContext context) {
        OrderInfo orderInfo = context.getOrderInfo();
        boolean alreadyWaiting = orderInfo.getOrderStatus() != null
                && orderInfo.getOrderStatus() == 3
                && orderInfo.getReceiveTime() != null;
        if (alreadyWaiting) {
            return;
        }
        if (orderInfo.getOrderStatus() == null || orderInfo.getOrderStatus() < 3) {
            orderInfo.setOrderStatus(3);
        }
        if (orderInfo.getReceiveTime() == null) {
            orderInfo.setReceiveTime(context.now());
        }
        context.saveOrder();
        context.sendAddMoneyMessage();
    }

    @Override
    public void confirm(OrderContext context) {
        OrderInfo orderInfo = context.getOrderInfo();
        if (orderInfo.getOrderStatus() == null || orderInfo.getOrderStatus() != 3) {
            throw new LianqingException("订单状态不正确，无法确认收货");
        }
        orderInfo.setOrderStatus(4);
        context.saveOrder();
        context.grantCompletionPoints();
    }
}
