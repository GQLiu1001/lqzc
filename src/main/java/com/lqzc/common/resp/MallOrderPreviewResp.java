package com.lqzc.common.resp;

import lombok.Data;
import java.math.BigDecimal;

/**
 * C端订单预览响应
 */
@Data
public class MallOrderPreviewResp {
    /** 商品总价 */
    private BigDecimal totalPrice;
    /** 配送费 */
    private BigDecimal deliveryFee;
    /** 优惠金额 */
    private BigDecimal discountAmount;
    /** 积分抵扣金额 */
    private BigDecimal pointsDeduction;
    /** 应付金额 */
    private BigDecimal payableAmount;
    /** 最优优惠券 */
    private OptimalCoupon optimalCoupon;
    
    @Data
    public static class OptimalCoupon {
        private Long id;
        private String title;
    }
}

