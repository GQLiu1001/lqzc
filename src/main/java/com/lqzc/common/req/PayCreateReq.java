package com.lqzc.common.req;

import lombok.Data;

@Data
public class PayCreateReq {
    /** 订单编号 */
    private String orderNo;
    /** 支付渠道：1微信 2支付宝 */
    private Integer channel;
}
