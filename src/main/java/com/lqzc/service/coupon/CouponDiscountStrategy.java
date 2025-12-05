package com.lqzc.service.coupon;

import com.lqzc.common.domain.CouponTemplate;

import java.math.BigDecimal;

/**
 * 优惠券折扣策略接口
 */
public interface CouponDiscountStrategy {

    /**
     * 对应的优惠券类型
     */
    int getType();

    /**
     * 当前优惠券在给定金额下是否可用
     */
    boolean canApply(CouponTemplate template, BigDecimal totalPrice);

    /**
     * 计算优惠金额（已校验可用性）
     */
    BigDecimal calculateDiscount(CouponTemplate template, BigDecimal totalPrice);
}
