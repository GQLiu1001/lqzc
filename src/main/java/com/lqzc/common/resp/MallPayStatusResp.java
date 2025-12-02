package com.lqzc.common.resp;

import lombok.Data;

/**
 * 支付状态响应
 */
@Data
public class MallPayStatusResp {
    /** 订单号 */
    private String orderNo;
    /** 支付状态：0=待支付 1=支付成功 2=支付失败 3=退款中 4=已退款 */
    private Integer payStatus;
    /** 支付时间 */
    private String payTime;
    /** 交易流水号 */
    private String transactionNo;
}

