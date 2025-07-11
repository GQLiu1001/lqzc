package com.lqzc.common.req;

import lombok.Data;

import java.math.BigDecimal;
@Data
public class OrderDispatchReq {
    private String orderNo;
    private String customerPhone;
    private String deliveryAddress;
    private BigDecimal deliveryFee;
    private BigDecimal goodsWeight;
    private String remark;
}
