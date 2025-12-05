package com.lqzc.service.coupon;

import com.lqzc.common.domain.CouponTemplate;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;

/**
 * 现金券策略（type=3）：直接立减固定金额。
 * 依赖父类校验有效期/门槛，额外校验金额为非负。
 */
@Component
public class CashCouponStrategy extends AbstractCouponDiscountStrategy {

    @Override
    public int getType() {
        return 3;
    }

    @Override
    protected boolean extraValidate(CouponTemplate template, BigDecimal totalPrice) {
        return template.getDiscountAmount() != null && template.getDiscountAmount().compareTo(BigDecimal.ZERO) >= 0;
    }

    @Override
    protected BigDecimal doCalculate(CouponTemplate template, BigDecimal totalPrice) {
        return template.getDiscountAmount();
    }
}
