package com.lqzc.common.records;

import lombok.Data;

import java.math.BigDecimal;
/**
 * OrderInfo的子字段
 * @author Rabbittank
 * @since 1.0.0
 */
@Data
public class DispatchOrderListRecord {
    /**
     * 配送订单ID
     */
    private Long id;

    /**
     * 订单编号
     */
    private String orderNo;

    /**
     * 司机ID
     */
    private Long driverId;

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

    /**
     * 配送备注
     */
    private String remark;

    /**
     * 创建时间
     */
    private String createTime;

    /**
     * 更新时间
     */
    private String updateTime;

    /**
     * 配送状态
     */
    private Integer dispatchStatus;
}
