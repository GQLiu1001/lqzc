package com.lqzc.common.resp;

import java.math.BigDecimal;
import lombok.Data;

@Data
public class OrderPreviewResp {
    /** 商品总价 */
    private BigDecimal totalPrice;
    /** 运费 */
    private BigDecimal deliveryFee;
    /** 优惠合计 */
    private BigDecimal discountAmount;
    /** 积分抵扣 */
    private BigDecimal pointsDeduction;
    /** 应付金额 */
    private BigDecimal payableAmount;
    /** 最优券信息 */
    private OptimalCoupon optimalCoupon;

    @Data
    public static class OptimalCoupon {
        /** 优惠券ID */
        private Long id;
        /** 标题 */
        private String title;
    }
}
