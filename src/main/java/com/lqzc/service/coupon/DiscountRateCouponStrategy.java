package com.lqzc.service.coupon;

import com.lqzc.common.domain.CouponTemplate;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;

/**
 * 折扣券策略（type=2）：按折扣率计算优惠金额，可设置优惠上限（maxDiscount）。
 * 校验折扣率必须 (0,1) 之间，防止无效或放大金额。
 */
@Component
public class DiscountRateCouponStrategy extends AbstractCouponDiscountStrategy {

    @Override
    public int getType() {
        return 2;
    }

    @Override
    protected boolean extraValidate(CouponTemplate template, BigDecimal totalPrice) {
        BigDecimal rate = template.getDiscountRate();
        return rate != null && rate.compareTo(BigDecimal.ZERO) > 0 && rate.compareTo(BigDecimal.ONE) < 0;
    }

    @Override
    protected BigDecimal doCalculate(CouponTemplate template, BigDecimal totalPrice) {
        BigDecimal rate = template.getDiscountRate();
        BigDecimal discount = totalPrice.multiply(BigDecimal.ONE.subtract(rate));
        if (template.getMaxDiscount() != null) {
            discount = discount.min(template.getMaxDiscount());
        }
        return discount;
    }
}
