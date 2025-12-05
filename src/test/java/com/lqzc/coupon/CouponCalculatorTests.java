package com.lqzc.coupon;

import com.lqzc.common.domain.CouponTemplate;
import com.lqzc.common.domain.CustomerCoupon;
import com.lqzc.service.coupon.CashCouponStrategy;
import com.lqzc.service.coupon.CouponCalculator;
import com.lqzc.service.coupon.DiscountRateCouponStrategy;
import com.lqzc.service.coupon.FullReductionCouponStrategy;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.Date;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class CouponCalculatorTests {

    private CouponCalculator calculator;

    @BeforeEach
    void setUp() {
        // 手动构造 CouponCalculator，等同于 Spring 的构造器注入。
        // 通过显式传入三种策略，确保：
        // 1) 每个策略的计算逻辑可以在不依赖 Spring 容器的情况下被单测覆盖；
        // 2) findBestCoupon 的策略分发顺序与真实运行环境一致；
        // 3) 单测不需要 Redis/DB 依赖即可验证金额计算正确性。
        calculator = new CouponCalculator(List.of(
                new FullReductionCouponStrategy(),
                new DiscountRateCouponStrategy(),
                new CashCouponStrategy()
        ));
    }

    @Test
    void fullReductionRespectsThreshold() {
        // 构造一张满减券：满 100-20，验证门槛判定和立减金额。
        CouponTemplate template = baseTemplate(1L, 1);
        template.setThresholdAmount(BigDecimal.valueOf(100));
        template.setDiscountAmount(BigDecimal.valueOf(20));

        // 未达到门槛的场景：策略应返回不可用且折扣为 0。
        assertFalse(calculator.canApply(template, BigDecimal.valueOf(80)));
        assertEquals(BigDecimal.ZERO, calculator.calculateDiscount(template, BigDecimal.valueOf(80)));

        // 达到门槛的场景：策略应判定可用并返回立减金额 20。
        assertTrue(calculator.canApply(template, BigDecimal.valueOf(120)));
        assertEquals(BigDecimal.valueOf(20), calculator.calculateDiscount(template, BigDecimal.valueOf(120)));
    }

    @Test
    void discountRateAppliesCap() {
        // 构造一张折扣券：9 折，封顶 6 元。
        // 验证：折扣计算后若超过封顶，应被截断到封顶值。
        CouponTemplate template = baseTemplate(2L, 2);
        template.setDiscountRate(BigDecimal.valueOf(0.9)); // 9折
        template.setMaxDiscount(BigDecimal.valueOf(6));

        // 69 元下单，理论优惠 6.9，超过上限，最终应为 6。
        BigDecimal discount = calculator.calculateDiscount(template, BigDecimal.valueOf(69));
        assertEquals(BigDecimal.valueOf(6), discount); // 6.9 -> capped to 6
    }

    @Test
    void bestCouponSelectionPicksMaximumDiscount() {
        // 准备两张券：满减 15 元 vs 8 折（上限 50），验证 findBestCoupon 选择最大优惠。
        CouponTemplate reduction = baseTemplate(10L, 1);
        reduction.setDiscountAmount(BigDecimal.valueOf(15));

        CouponTemplate discount = baseTemplate(11L, 2);
        discount.setDiscountRate(BigDecimal.valueOf(0.8)); // 8折
        discount.setMaxDiscount(BigDecimal.valueOf(50));

        CustomerCoupon couponA = new CustomerCoupon();
        couponA.setId(100L);
        couponA.setTemplateId(reduction.getId());

        CustomerCoupon couponB = new CustomerCoupon();
        couponB.setId(101L);
        couponB.setTemplateId(discount.getId());

        Map<Long, CouponTemplate> templateMap = Map.of(
                reduction.getId(), reduction,
                discount.getId(), discount
        );

        // 订单 200 元，折扣券优惠 40 元 > 满减券 15 元，应选择折扣券。
        var best = calculator.findBestCoupon(
                List.of(couponA, couponB),
                templateMap,
                BigDecimal.valueOf(200)
        );

        assertTrue(best.isPresent());
        assertEquals(discount.getId(), best.get().template().getId());
        assertEquals(0, BigDecimal.valueOf(40).compareTo(best.get().discount())); // 200 * (1-0.8)
    }

    private CouponTemplate baseTemplate(Long id, Integer type) {
        // 构造一个基础模板，设置：
        // - ID 与类型（匹配具体策略）
        // - 有效期覆盖当前时间，避免因时间校验导致策略不可用
        // 其他字段由各测试按需补充。
        CouponTemplate template = new CouponTemplate();
        template.setId(id);
        template.setType(type);
        template.setValidFrom(new Date(System.currentTimeMillis() - 3600_000));
        template.setValidTo(new Date(System.currentTimeMillis() + 3600_000));
        return template;
    }
}
