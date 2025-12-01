package com.lqzc.common.records;

import lombok.Data;

import java.math.BigDecimal;
import java.util.Date;

/**
 * 订单信息记录类
 * OrderInfo的子字段和其子订单数量subOrderCount
 * @author Rabbittank
 * @since 1.0.0
 */
@Data
public class OrderInfoRecords {
    /**/
    private Long id;
    private String orderNo;
    private Long customerId;
    private String customerPhone;
    private Integer orderSource;
    private BigDecimal totalPrice;
    private BigDecimal payableAmount;
    private BigDecimal discountAmount;
    private Integer dispatchStatus;
    private Integer orderStatus;
    private Integer payStatus;
    private Integer payChannel;
    private Date payTime;
    private BigDecimal deliveryFee;
    private Long driverId;
    private String deliveryAddress;
    private Long addressId;
    private BigDecimal goodsWeight;
    private Long couponId;
    private Integer pointsUsed;
    private Date expectedDeliveryTime;
    private Date receiveTime;
    private String remark;
    private String cancelReason;
    private Integer version;
    private Date createTime;
    private Date updateTime;
    /**
     * 子订单数量
     */
    private Integer subOrderCount;
}
