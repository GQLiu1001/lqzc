package com.lqzc.common.resp;

import java.math.BigDecimal;
import lombok.Data;

@Data
public class CouponMarketItemResp {
    /** 模板ID */
    private Long id;
    /** 标题 */
    private String title;
    /** 类型：1满减 2折扣 3现金 */
    private Integer type;
    /** 门槛金额 */
    private BigDecimal thresholdAmount;
    /** 立减金额 */
    private BigDecimal discountAmount;
    /** 折扣率 */
    private BigDecimal discountRate;
    /** 折扣封顶 */
    private BigDecimal maxDiscount;
    /** 有效期起 */
    private String validFrom;
    /** 有效期止 */
    private String validTo;
    /** 是否已领取 */
    private Boolean isReceived;
}
