package com.lqzc.config;

import com.alibaba.csp.sentinel.annotation.aspectj.SentinelResourceAspect;
import com.alibaba.csp.sentinel.slots.block.RuleConstant;
import com.alibaba.csp.sentinel.slots.block.degrade.DegradeRule;
import com.alibaba.csp.sentinel.slots.block.degrade.DegradeRuleManager;
import com.alibaba.csp.sentinel.slots.block.degrade.circuitbreaker.CircuitBreakerStrategy;
import com.alibaba.csp.sentinel.slots.block.flow.FlowRule;
import com.alibaba.csp.sentinel.slots.block.flow.FlowRuleManager;
import com.alibaba.csp.sentinel.slots.block.flow.param.ParamFlowRule;
import com.alibaba.csp.sentinel.slots.block.flow.param.ParamFlowRuleManager;
import com.lqzc.common.props.CouponSentinelProps;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

/**
 * 抢券接口 Sentinel 规则配置
 */
@Configuration
@RequiredArgsConstructor
@Slf4j
public class CouponSentinelConfig {

    public static final String COUPON_RECEIVE_RESOURCE = "mallCouponReceive";

    private final CouponSentinelProps couponSentinelProps;

    @Bean
    public SentinelResourceAspect sentinelResourceAspect() {
        return new SentinelResourceAspect();
    }

    @PostConstruct
    public void initRules() {
        // 抢券接口整体QPS限流
        FlowRule receiveFlowRule = new FlowRule(COUPON_RECEIVE_RESOURCE);
        receiveFlowRule.setGrade(RuleConstant.FLOW_GRADE_QPS);
        receiveFlowRule.setCount(couponSentinelProps.getReceiveQps());

        // 按优惠券模板ID做热点限流，避免单个爆款券把整体链路打满
        ParamFlowRule templateHotspotRule = new ParamFlowRule(COUPON_RECEIVE_RESOURCE);
        templateHotspotRule.setParamIdx(0);
        templateHotspotRule.setCount(couponSentinelProps.getTemplateHotspotQps());
        templateHotspotRule.setDurationInSec(1);

        // 慢调用熔断，请求RT持续抖高时直接保护下游
        DegradeRule slowRequestRule = new DegradeRule(COUPON_RECEIVE_RESOURCE);
        slowRequestRule.setGrade(CircuitBreakerStrategy.SLOW_REQUEST_RATIO.getType());
        slowRequestRule.setCount(couponSentinelProps.getSlowRequestMs());
        slowRequestRule.setSlowRatioThreshold(couponSentinelProps.getSlowRequestRatioThreshold());
        slowRequestRule.setMinRequestAmount(couponSentinelProps.getMinRequestAmount());
        slowRequestRule.setStatIntervalMs(couponSentinelProps.getStatIntervalMs());
        slowRequestRule.setTimeWindow(couponSentinelProps.getCircuitBreakSeconds());

        // 异常比例熔断，Redis/MQ出现抖动时快速失败
        DegradeRule exceptionRatioRule = new DegradeRule(COUPON_RECEIVE_RESOURCE);
        exceptionRatioRule.setGrade(CircuitBreakerStrategy.ERROR_RATIO.getType());
        exceptionRatioRule.setCount(couponSentinelProps.getExceptionRatioThreshold());
        exceptionRatioRule.setMinRequestAmount(couponSentinelProps.getMinRequestAmount());
        exceptionRatioRule.setStatIntervalMs(couponSentinelProps.getStatIntervalMs());
        exceptionRatioRule.setTimeWindow(couponSentinelProps.getCircuitBreakSeconds());

        FlowRuleManager.loadRules(List.of(receiveFlowRule));
        ParamFlowRuleManager.loadRules(List.of(templateHotspotRule));
        DegradeRuleManager.loadRules(List.of(slowRequestRule, exceptionRatioRule));

        log.info(
                "Sentinel规则加载完成: resource={}, receiveQps={}, templateHotspotQps={}, slowRequestMs={}, slowRatio={}, exceptionRatio={}",
                COUPON_RECEIVE_RESOURCE,
                couponSentinelProps.getReceiveQps(),
                couponSentinelProps.getTemplateHotspotQps(),
                couponSentinelProps.getSlowRequestMs(),
                couponSentinelProps.getSlowRequestRatioThreshold(),
                couponSentinelProps.getExceptionRatioThreshold()
        );
    }
}
