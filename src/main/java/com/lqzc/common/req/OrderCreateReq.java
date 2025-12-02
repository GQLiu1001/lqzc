package com.lqzc.common.req;

import java.util.List;
import lombok.Data;

@Data
public class OrderCreateReq {
    /** 收货地址ID */
    private Long addressId;
    /** 优惠券ID，可为空 */
    private Long couponId;
    /** 使用积分数量 */
    private Integer pointsUsed;
    /** 备注 */
    private String remark;
    /** 商品项 */
    private List<OrderItemReq> items;
}
