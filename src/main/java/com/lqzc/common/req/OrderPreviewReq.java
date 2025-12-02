package com.lqzc.common.req;

import java.util.List;
import lombok.Data;

@Data
public class OrderPreviewReq {
    /** 商品项列表 */
    private List<OrderItemReq> items;
    /** 指定优惠券，可为空 */
    private Long couponId;
    /** 是否使用积分抵扣 */
    private Boolean usePoints;
}
