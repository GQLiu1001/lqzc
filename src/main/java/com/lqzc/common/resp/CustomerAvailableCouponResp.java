package com.lqzc.common.resp;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Data;

import java.math.BigDecimal;

/**
 * 用户可用优惠券响应DTO
 * 用于后台派单时选择优惠券
 */
@Data
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CustomerAvailableCouponResp {
    
    /**
     * 优惠券ID（customer_coupon表的id）
     */
    private Long couponId;
    
    /**
     * 优惠券标题
     */
    private String title;
    
    /**
     * 类型：1满减 2折扣 3现金券
     */
    private Integer type;
    
    /**
     * 使用门槛金额
     */
    private BigDecimal thresholdAmount;
    
    /**
     * 优惠金额（满减/现金券）
     */
    private BigDecimal discountAmount;
    
    /**
     * 折扣比例（折扣券，如80表示8折）
     */
    private BigDecimal discountRate;
    
    /**
     * 最大优惠金额（折扣券）
     */
    private BigDecimal maxDiscount;
    
    /**
     * 过期时间
     */
    private String expireTime;
    
    /**
     * 根据订单金额计算的实际优惠金额
     */
    private BigDecimal calculatedDiscount;
    
    /**
     * 是否可用（满足门槛条件）
     */
    private Boolean usable;
}

