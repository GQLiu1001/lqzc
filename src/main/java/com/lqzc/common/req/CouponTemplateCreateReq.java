package com.lqzc.common.req;

import java.math.BigDecimal;
import java.util.Date;
import lombok.Data;

@Data
public class CouponTemplateCreateReq {
    /** 标题 */
    private String title;
    /** 类型：1满减 2折扣 3现金 */
    private Integer type;
    /** 使用门槛 */
    private BigDecimal thresholdAmount;
    /** 立减金额 */
    private BigDecimal discountAmount;
    /** 折扣率 */
    private BigDecimal discountRate;
    /** 折扣封顶 */
    private BigDecimal maxDiscount;
    /** 发行总量 */
    private Integer totalIssued;
    /** 每人限领 */
    private Integer perUserLimit;
    /** 有效期开始 */
    private Date validFrom;
    /** 有效期结束 */
    private Date validTo;
}
