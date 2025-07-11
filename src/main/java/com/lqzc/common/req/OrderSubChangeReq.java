package com.lqzc.common.req;

import lombok.Data;
import java.math.BigDecimal;

/**
 * 添加订单项请求类
 */
@Data
public class OrderSubChangeReq {
    /**
     * orderDetailID
     *
     */
    private Long id;

    /**
     * orderInfoID
     *
     */
    private Long orderId;

    /**
     * 库存商品ID
     *
     */
    private Long itemId;

    /**
     * 购买数量
     */
    private Integer amount;
    
    /**
     * 小计金额
     */
    private BigDecimal subtotalPrice;

    /**
     * 操作类型
     * 0：修改 1：添加 2：删除
     */
    private Integer changeType;
}
