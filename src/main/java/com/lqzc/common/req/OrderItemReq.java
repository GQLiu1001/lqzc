package com.lqzc.common.req;

import lombok.Data;

@Data
public class OrderItemReq {
    /** 商品ID */
    private Long itemId;
    /** 购买数量 */
    private Integer amount;
}
