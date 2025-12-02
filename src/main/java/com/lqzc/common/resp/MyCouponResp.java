package com.lqzc.common.resp;

import lombok.Data;
import java.math.BigDecimal;

/**
 * 我的优惠券响应
 */
@Data
public class MyCouponResp {
    /** 券ID */
    private Long id;
    /** 模板ID */
    private Long templateId;
    /** 优惠券标题 */
    private String title;
    /** 券码 */
    private String code;
    /** 状态：0未使用 1已使用 2已过期 3已作废 */
    private Integer status;
    /** 过期时间 */
    private String expireTime;
    /** 类型：1=满减 2=折扣 3=现金券 */
    private Integer type;
    /** 使用门槛金额 */
    private BigDecimal thresholdAmount;
    /** 立减金额 */
    private BigDecimal discountAmount;
    /** 折扣率 */
    private BigDecimal discountRate;
}
