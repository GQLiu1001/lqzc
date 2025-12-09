package com.lqzc.order;

import com.lqzc.common.constant.DispatchConstant;
import com.lqzc.common.domain.OrderInfo;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.order.state.*;
import org.springframework.stereotype.Component;

/**
 * @author rabbittank
 * @description 工厂：根据订单的主状态/派送状态返回对应的状态处理器
 * @createDate 2025-12-10 00:00:00
 */
@Component
public class OrderStateFactory {

    public OrderState getState(OrderInfo orderInfo) {
        if (orderInfo == null) {
            throw new LianqingException("订单不存在");
        }

        Integer orderStatus = orderInfo.getOrderStatus();
        Integer dispatchStatus = orderInfo.getDispatchStatus();

        if (orderStatus != null) {
            if (orderStatus == 3) {
                return new WaitingConfirmState();
            }
            if (orderStatus == 4) {
                if (dispatchStatus != null && dispatchStatus.equals(DispatchConstant.FINISH_DISPATCH)) {
                    return new CompletedState();
                }
                return new ClosedState();
            }
            if (orderStatus >= 5) {
                return new ClosedState();
            }
        }

        if (dispatchStatus != null) {
            if (dispatchStatus.equals(DispatchConstant.WAITING_DISPATCH)) {
                return new WaitingDispatchState();
            }
            if (dispatchStatus.equals(DispatchConstant.WAITING_DRIVER) ||
                    dispatchStatus.equals(DispatchConstant.DISPATCHING)) {
                return new DispatchingState();
            }
            if (dispatchStatus.equals(DispatchConstant.FINISH_DISPATCH)) {
                return new WaitingConfirmState();
            }
        }

        throw new LianqingException("无法匹配订单状态处理器");
    }
}
