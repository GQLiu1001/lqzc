package com.lqzc.common.req;

import lombok.Data;

/**
 * C端发起支付请求
 */
@Data
public class MallPayCreateReq {
    /** 订单号 */
    private String orderNo;
    /** 支付渠道：1=微信 2=支付宝 */
    private Integer channel;
}

