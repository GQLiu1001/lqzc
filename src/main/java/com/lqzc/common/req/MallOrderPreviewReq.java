package com.lqzc.common.req;

import lombok.Data;
import java.util.List;

/**
 * C端订单预览请求
 */
@Data
public class MallOrderPreviewReq {
    /** 商品列表 */
    private List<OrderItem> items;
    /** 指定优惠券ID（可选） */
    private Long couponId;
    /** 是否使用积分抵扣 */
    private Boolean usePoints;
    
    @Data
    public static class OrderItem {
        /** 商品ID */
        private Long itemId;
        /** 数量 */
        private Integer amount;
    }
}

