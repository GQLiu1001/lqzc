package com.lqzc.common.resp;

import java.math.BigDecimal;
import java.util.Date;
import lombok.Data;

/**
 * 优惠券模板列表响应
 * <p>
 * 包含优惠券模板基础信息以及统计数据（已领取、已核销数量）
 * </p>
 */
@Data
public class CouponTemplateListResp {
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
    /** 折扣率（0.90代表9折） */
    private BigDecimal discountRate;
    /** 折扣封顶 */
    private BigDecimal maxDiscount;
    /** 有效期开始 */
    private Date validFrom;
    /** 有效期结束 */
    private Date validTo;
    /** 发行总量 */
    private Integer totalIssued;
    /** 每人限领 */
    private Integer perUserLimit;
    /** 状态：1启用 0停用 */
    private Integer status;
    /** 已领取数量 */
    private Integer receivedCount;
    /** 已核销数量（已使用） */
    private Integer usedCount;
    /** 创建时间 */
    private Date createTime;
}

