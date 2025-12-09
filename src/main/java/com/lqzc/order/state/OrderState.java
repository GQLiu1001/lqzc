package com.lqzc.order.state;

import com.lqzc.common.exception.LianqingException;
import com.lqzc.order.OrderContext;
import com.lqzc.order.domain.OrderLifecycleState;

/**
 * @author rabbittank
 * @description 订单状态处理器顶层接口，每个具体状态实现自身允许的动作
 * @createDate 2025-12-10 00:00:00
 */
public interface OrderState {

    /**
     * 返回当前处理器对应的生命周期标识。
     */
    OrderLifecycleState getName();

    /**
     * 进入当前状态时的钩子，用于处理入场副作用（默认空实现）。
     */
    default void onEnter(OrderContext context) {
        // 默认无操作
    }

    /**
     * 执行标准流转，如“派送中 -> 待确认”。
     */
    default void next(OrderContext context) {
        throw new LianqingException("状态 " + getName() + " 不支持此操作");
    }

    /**
     * 确认收货等终态动作。
     */
    default void confirm(OrderContext context) {
        throw new LianqingException("状态 " + getName() + " 不支持确认操作");
    }

    /**
     * 关闭/取消订单。
     */
    default void close(OrderContext context, String reason) {
        throw new LianqingException("状态 " + getName() + " 不支持关闭操作");
    }
}
