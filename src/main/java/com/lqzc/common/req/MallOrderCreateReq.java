package com.lqzc.common.req;

import lombok.Data;
import java.util.List;

/**
 * C端创建订单请求
 */
@Data
public class MallOrderCreateReq {
    /** 收货地址ID */
    private Long addressId;
    /** 优惠券ID（可选） */
    private Long couponId;
    /** 使用积分（可选） */
    private Integer pointsUsed;
    /** 备注 */
    private String remark;
    /** 商品列表 */
    private List<OrderItem> items;
    
    @Data
    public static class OrderItem {
        /** 商品ID */
        private Long itemId;
        /** 数量 */
        private Integer amount;
    }
}

