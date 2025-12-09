package com.lqzc.order.domain;

/**
 * @author rabbittank
 * @description 订单生命周期状态枚举，便于状态处理器标识自身类型
 * @createDate 2025-12-10 00:00:00
 */
public enum OrderLifecycleState {
    /** 待派单/待发货 */
    WAITING_DISPATCH,
    /** 待接单或派送中 */
    DISPATCHING,
    /** 已送达，待确认收货 */
    WAITING_CONFIRM,
    /** 已完成 */
    COMPLETED,
    /** 已关闭/已取消/异常终止 */
    CLOSED
}
