package com.lqzc.common.resp;

import lombok.Data;

@Data
public class PayStatusResp {
    /** 订单编号 */
    private String orderNo;
    /** 支付状态 */
    private Integer payStatus;
    /** 支付时间 */
    private String payTime;
    /** 第三方交易号 */
    private String transactionNo;
}
