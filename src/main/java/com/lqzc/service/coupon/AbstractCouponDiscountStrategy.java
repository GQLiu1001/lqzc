package com.lqzc.service.coupon;

import com.lqzc.common.domain.CouponTemplate;

import java.math.BigDecimal;
import java.util.Date;

/**
 * 模板方法：统一处理通用校验（类型匹配、有效期、门槛）后，再委派子类计算优惠。
 * 这样可以避免每个策略重复写“是否可用”的条件判断，同时保持可扩展性：
 * - canApply 先跑通用校验，再调用 extraValidate 覆盖策略特有的前置条件
 * - calculateDiscount 只在可用时计算，防止重复校验
 */
public abstract class AbstractCouponDiscountStrategy implements CouponDiscountStrategy {

    @Override
    public boolean canApply(CouponTemplate template, BigDecimal totalPrice) {
        if (template == null || totalPrice == null) {
            return false;
        }
        if (template.getType() == null || template.getType() != getType()) {
            return false;
        }

        Date now = new Date();
        if (template.getValidFrom() != null && now.before(template.getValidFrom())) {
            return false;
        }
        if (template.getValidTo() != null && now.after(template.getValidTo())) {
            return false;
        }
        if (template.getThresholdAmount() != null && totalPrice.compareTo(template.getThresholdAmount()) < 0) {
            return false;
        }
        return extraValidate(template, totalPrice);
    }

    @Override
    public BigDecimal calculateDiscount(CouponTemplate template, BigDecimal totalPrice) {
        if (!canApply(template, totalPrice)) {
            return BigDecimal.ZERO;
        }
        BigDecimal discount = doCalculate(template, totalPrice);
        return discount != null ? discount.max(BigDecimal.ZERO) : BigDecimal.ZERO;
    }

    /**
     * 子类额外校验
     */
    protected boolean extraValidate(CouponTemplate template, BigDecimal totalPrice) {
        return true;
    }

    /**
     * 子类实现具体计算逻辑
     */
    protected abstract BigDecimal doCalculate(CouponTemplate template, BigDecimal totalPrice);
}
