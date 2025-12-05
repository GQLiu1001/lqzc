package com.lqzc.service.coupon;

import com.lqzc.common.domain.CouponTemplate;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;

/**
 * 满减券策略（type=1）：达到阈值后立减固定金额。
 * 依赖父类完成门槛/有效期校验，额外校验减免金额为非负。
 */
@Component
public class FullReductionCouponStrategy extends AbstractCouponDiscountStrategy {

    @Override
    public int getType() {
        return 1;
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
