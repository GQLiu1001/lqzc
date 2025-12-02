package com.lqzc.common.resp;

import java.math.BigDecimal;
import lombok.Data;

@Data
public class OrderCreateResp {
    /** 订单编号 */
    private String orderNo;
    /** 应付金额 */
    private BigDecimal payableAmount;
    /** 支付截止时间 */
    private String expireTime;
}
