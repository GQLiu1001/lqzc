package com.lqzc.common.resp;

import com.lqzc.common.domain.OrderDetail;
import lombok.Data;
import java.math.BigDecimal;
import java.util.Date;
import java.util.List;

/**
 * 订单详情响应类
 * OrderInfo 以及相应的 子订单List:OrderDetail subOrder
 */
@Data
public class OrderDetailResp {
    /**
     * 订单ID
     */
    private Long id;
    
    /**
     * 订单编号
     */
    private String orderNo;
    
    /**
     * 前台客户ID
     */
    private Long customerId;
    
    /**
     * 客户手机号
     */
    private String customerPhone;
    
    /**
     * 订单来源
     */
    private Integer orderSource;
    
    /**
     * 订单总金额
     */
    private BigDecimal totalPrice;
    
    /**
     * 应付金额
     */
    private BigDecimal payableAmount;
    
    /**
     * 优惠合计
     */
    private BigDecimal discountAmount;
    
    /**
     * 订单派送状态：0=待派送 1=待接单 2=派送中 3=已完成
     */
    private Integer dispatchStatus;
    
    /**
     * 订单状态
     */
    private Integer orderStatus;
    
    /**
     * 支付状态
     */
    private Integer payStatus;
    
    /**
     * 支付渠道
     */
    private Integer payChannel;
    
    /**
     * 支付时间
     */
    private Date payTime;
    
    /**
     * 配送费用
     */
    private BigDecimal deliveryFee;
    
    /**
     * 司机ID
     */
    private Long driverId;
    
    /**
     * 派送地址
     */
    private String deliveryAddress;
    
    /**
     * 收货地址ID
     */
    private Long addressId;
    
    /**
     * 货物重量(吨)
     */
    private BigDecimal goodsWeight;
    
    /**
     * 使用的优惠券ID
     */
    private Long couponId;
    
    /**
     * 抵扣积分
     */
    private Integer pointsUsed;
    
    /**
     * 期望送达时间
     */
    private Date expectedDeliveryTime;
    
    /**
     * 签收时间
     */
    private Date receiveTime;
    
    /**
     * 创建时间
     */
    private Date createTime;
    
    /**
     * 更新时间
     */
    private Date updateTime;
    
    /**
     * 子订单列表
     */
    private List<OrderDetail> subOrder;
    
    /**
     * 订单备注
     */
    private String remark;

    /**
     * 取消原因
     */
    private String cancelReason;

    /**
     * 版本号
     */
    private Integer version;

}
