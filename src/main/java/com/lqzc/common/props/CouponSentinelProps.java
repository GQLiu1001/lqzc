package com.lqzc.common.props;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * 抢券接口 Sentinel 配置
 */
@Data
@Component
@ConfigurationProperties(prefix = "lqzc.coupon.sentinel")
public class CouponSentinelProps {

    /** 抢券接口整体QPS阈值 */
    private double receiveQps = 600D;

    /** 单个优惠券模板热点参数QPS阈值 */
    private double templateHotspotQps = 300D;

    /** 慢调用判定RT阈值（毫秒） */
    private int slowRequestMs = 200;

    /** 慢调用比例熔断阈值 */
    private double slowRequestRatioThreshold = 0.5D;

    /** 异常比例熔断阈值 */
    private double exceptionRatioThreshold = 0.4D;

    /** 熔断生效前的最小请求数 */
    private int minRequestAmount = 20;

    /** 统计窗口（毫秒） */
    private int statIntervalMs = 10000;

    /** 熔断恢复时间（秒） */
    private int circuitBreakSeconds = 10;
}
