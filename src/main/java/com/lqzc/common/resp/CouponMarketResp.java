package com.lqzc.common.resp;

import lombok.Data;
import java.math.BigDecimal;

/**
 * 领券中心优惠券响应
 */
@Data
public class CouponMarketResp {
    /** 模板ID */
    private Long id;
    /** 优惠券标题 */
    private String title;
    /** 类型：1=满减 2=折扣 3=现金券 */
    private Integer type;
    /** 使用门槛金额 */
    private BigDecimal thresholdAmount;
    /** 立减金额 */
    private BigDecimal discountAmount;
    /** 折扣率 */
    private BigDecimal discountRate;
    /** 折扣封顶 */
    private BigDecimal maxDiscount;
    /** 有效期开始 */
    private String validFrom;
    /** 有效期结束 */
    private String validTo;
    /** 当前用户是否已领 */
    private Boolean isReceived;
}

