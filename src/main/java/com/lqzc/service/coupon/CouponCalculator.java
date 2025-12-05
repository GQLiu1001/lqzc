package com.lqzc.service.coupon;

import com.lqzc.common.domain.CouponTemplate;
import com.lqzc.common.domain.CustomerCoupon;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * 优惠券计算器：负责策略分发与最优券选择。
 * 职责拆分：
 * 1) 通过优惠券类型找到对应策略（策略模式）
 * 2) 对外暴露统一的校验与计算接口，屏蔽具体券种差异
 * 3) findBestCoupon 在用户持有的多张券中计算最大优惠金额，返回最优券+优惠值
 */
@Service
public class CouponCalculator {

    private final Map<Integer, CouponDiscountStrategy> strategyMap;

    public CouponCalculator(List<CouponDiscountStrategy> strategies) {
        this.strategyMap = strategies.stream()
                .collect(Collectors.toMap(CouponDiscountStrategy::getType, Function.identity()));
    }

    public boolean canApply(CouponTemplate template, BigDecimal totalPrice) {
        return findStrategy(template)
                .map(strategy -> strategy.canApply(template, totalPrice))
                .orElse(false);
    }

    public BigDecimal calculateDiscount(CouponTemplate template, BigDecimal totalPrice) {
        return findStrategy(template)
                .map(strategy -> strategy.calculateDiscount(template, totalPrice))
                .orElse(BigDecimal.ZERO);
    }

    /**
     * 在给定的用户券中挑选最佳优惠券
     */
    public Optional<BestCoupon> findBestCoupon(List<CustomerCoupon> coupons,
                                               Map<Long, CouponTemplate> templateMap,
                                               BigDecimal totalPrice) {
        if (coupons == null || coupons.isEmpty()) {
            return Optional.empty();
        }
        BigDecimal best = BigDecimal.ZERO;
        BestCoupon bestCoupon = null;

        for (CustomerCoupon coupon : coupons) {
            CouponTemplate template = templateMap.get(coupon.getTemplateId());
            if (template == null) {
                continue;
            }
            BigDecimal discount = calculateDiscount(template, totalPrice);
            if (discount.compareTo(best) > 0) {
                best = discount;
                bestCoupon = new BestCoupon(coupon, template, discount);
            }
        }
        return Optional.ofNullable(bestCoupon);
    }

    private Optional<CouponDiscountStrategy> findStrategy(CouponTemplate template) {
        if (template == null || template.getType() == null) {
            return Optional.empty();
        }
        return Optional.ofNullable(strategyMap.get(template.getType()));
    }

    public record BestCoupon(CustomerCoupon coupon, CouponTemplate template, BigDecimal discount) {
    }
}
