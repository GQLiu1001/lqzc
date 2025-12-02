package com.lqzc.common.resp;

import lombok.Data;

@Data
public class PayCreateResp {
    /** 支付状态 */
    private Integer payStatus;
    /** 支付时间 */
    private String payTime;
}
