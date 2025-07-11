package com.lqzc.common.records;

import lombok.Data;

import java.math.BigDecimal;
import java.util.Date;

@Data
public class DispatchOrderFetchRecords {
    /**
     * 订单编号
     */
    private String orderNo;

    /**
     * 客户手机号
     */
    private String customerPhone;

    /**
     * 派送地址
     */
    private String deliveryAddress;

    /**
     * 配送费用
     */
    private BigDecimal deliveryFee;

    /**
     * 货物重量(吨)
     */
    private BigDecimal goodsWeight;

    private Date createTime;

    /**
     * 配送备注
     */
    private String remark;
}
