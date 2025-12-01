package com.lqzc.common.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.util.Date;
import lombok.Data;

/**
 * 订单主表
 * @TableName order_info
 */
@TableName(value ="order_info")
@Data
public class OrderInfo {
    /**
     * 订单ID
     */
    @TableId(type = IdType.AUTO)
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
     * 订单来源(1=前台商城 2=管理后台 3=司机端)
     */
    private Integer orderSource;

    /**
     * 订单总金额(原始金额)
     */
    private BigDecimal totalPrice;

    /**
     * 应付金额(扣除优惠后)
     */
    private BigDecimal payableAmount;

    /**
     * 优惠合计(积分/券)
     */
    private BigDecimal discountAmount;

    /**
     * 订单派送状态：0=待派送 1=待接单 2=派送中 3=已完成
     */
    private Integer dispatchStatus;

    /**
     * 订单状态：0=待支付 1=待发货 2=待收货 3=已完成 4=已取消 5=已关闭
     */
    private Integer orderStatus;

    /**
     * 支付状态：0=未支付 1=已支付 2=部分退款 3=已退款
     */
    private Integer payStatus;

    /**
     * 支付渠道：1=微信 2=支付宝 3=银行卡 4=线下
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
     * 收货地址ID快照
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

    /**
     * 订单创建时间
     */
    private Date createTime;

    /**
     * 订单更新时间
     */
    private Date updateTime;

    @Override
    public boolean equals(Object that) {
        if (this == that) {
            return true;
        }
        if (that == null) {
            return false;
        }
        if (getClass() != that.getClass()) {
            return false;
        }
        OrderInfo other = (OrderInfo) that;
        return (this.getId() == null ? other.getId() == null : this.getId().equals(other.getId()))
            && (this.getOrderNo() == null ? other.getOrderNo() == null : this.getOrderNo().equals(other.getOrderNo()))
            && (this.getCustomerId() == null ? other.getCustomerId() == null : this.getCustomerId().equals(other.getCustomerId()))
            && (this.getCustomerPhone() == null ? other.getCustomerPhone() == null : this.getCustomerPhone().equals(other.getCustomerPhone()))
            && (this.getOrderSource() == null ? other.getOrderSource() == null : this.getOrderSource().equals(other.getOrderSource()))
            && (this.getTotalPrice() == null ? other.getTotalPrice() == null : this.getTotalPrice().equals(other.getTotalPrice()))
            && (this.getPayableAmount() == null ? other.getPayableAmount() == null : this.getPayableAmount().equals(other.getPayableAmount()))
            && (this.getDiscountAmount() == null ? other.getDiscountAmount() == null : this.getDiscountAmount().equals(other.getDiscountAmount()))
            && (this.getDispatchStatus() == null ? other.getDispatchStatus() == null : this.getDispatchStatus().equals(other.getDispatchStatus()))
            && (this.getOrderStatus() == null ? other.getOrderStatus() == null : this.getOrderStatus().equals(other.getOrderStatus()))
            && (this.getPayStatus() == null ? other.getPayStatus() == null : this.getPayStatus().equals(other.getPayStatus()))
            && (this.getPayChannel() == null ? other.getPayChannel() == null : this.getPayChannel().equals(other.getPayChannel()))
            && (this.getPayTime() == null ? other.getPayTime() == null : this.getPayTime().equals(other.getPayTime()))
            && (this.getDeliveryFee() == null ? other.getDeliveryFee() == null : this.getDeliveryFee().equals(other.getDeliveryFee()))
            && (this.getDriverId() == null ? other.getDriverId() == null : this.getDriverId().equals(other.getDriverId()))
            && (this.getDeliveryAddress() == null ? other.getDeliveryAddress() == null : this.getDeliveryAddress().equals(other.getDeliveryAddress()))
            && (this.getAddressId() == null ? other.getAddressId() == null : this.getAddressId().equals(other.getAddressId()))
            && (this.getGoodsWeight() == null ? other.getGoodsWeight() == null : this.getGoodsWeight().equals(other.getGoodsWeight()))
            && (this.getCouponId() == null ? other.getCouponId() == null : this.getCouponId().equals(other.getCouponId()))
            && (this.getPointsUsed() == null ? other.getPointsUsed() == null : this.getPointsUsed().equals(other.getPointsUsed()))
            && (this.getExpectedDeliveryTime() == null ? other.getExpectedDeliveryTime() == null : this.getExpectedDeliveryTime().equals(other.getExpectedDeliveryTime()))
            && (this.getReceiveTime() == null ? other.getReceiveTime() == null : this.getReceiveTime().equals(other.getReceiveTime()))
            && (this.getRemark() == null ? other.getRemark() == null : this.getRemark().equals(other.getRemark()))
            && (this.getCancelReason() == null ? other.getCancelReason() == null : this.getCancelReason().equals(other.getCancelReason()))
            && (this.getVersion() == null ? other.getVersion() == null : this.getVersion().equals(other.getVersion()))
            && (this.getCreateTime() == null ? other.getCreateTime() == null : this.getCreateTime().equals(other.getCreateTime()))
            && (this.getUpdateTime() == null ? other.getUpdateTime() == null : this.getUpdateTime().equals(other.getUpdateTime()));
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int result = 1;
        result = prime * result + ((getId() == null) ? 0 : getId().hashCode());
        result = prime * result + ((getOrderNo() == null) ? 0 : getOrderNo().hashCode());
        result = prime * result + ((getCustomerId() == null) ? 0 : getCustomerId().hashCode());
        result = prime * result + ((getCustomerPhone() == null) ? 0 : getCustomerPhone().hashCode());
        result = prime * result + ((getOrderSource() == null) ? 0 : getOrderSource().hashCode());
        result = prime * result + ((getTotalPrice() == null) ? 0 : getTotalPrice().hashCode());
        result = prime * result + ((getPayableAmount() == null) ? 0 : getPayableAmount().hashCode());
        result = prime * result + ((getDiscountAmount() == null) ? 0 : getDiscountAmount().hashCode());
        result = prime * result + ((getDispatchStatus() == null) ? 0 : getDispatchStatus().hashCode());
        result = prime * result + ((getOrderStatus() == null) ? 0 : getOrderStatus().hashCode());
        result = prime * result + ((getPayStatus() == null) ? 0 : getPayStatus().hashCode());
        result = prime * result + ((getPayChannel() == null) ? 0 : getPayChannel().hashCode());
        result = prime * result + ((getPayTime() == null) ? 0 : getPayTime().hashCode());
        result = prime * result + ((getDeliveryFee() == null) ? 0 : getDeliveryFee().hashCode());
        result = prime * result + ((getDriverId() == null) ? 0 : getDriverId().hashCode());
        result = prime * result + ((getDeliveryAddress() == null) ? 0 : getDeliveryAddress().hashCode());
        result = prime * result + ((getAddressId() == null) ? 0 : getAddressId().hashCode());
        result = prime * result + ((getGoodsWeight() == null) ? 0 : getGoodsWeight().hashCode());
        result = prime * result + ((getCouponId() == null) ? 0 : getCouponId().hashCode());
        result = prime * result + ((getPointsUsed() == null) ? 0 : getPointsUsed().hashCode());
        result = prime * result + ((getExpectedDeliveryTime() == null) ? 0 : getExpectedDeliveryTime().hashCode());
        result = prime * result + ((getReceiveTime() == null) ? 0 : getReceiveTime().hashCode());
        result = prime * result + ((getRemark() == null) ? 0 : getRemark().hashCode());
        result = prime * result + ((getCancelReason() == null) ? 0 : getCancelReason().hashCode());
        result = prime * result + ((getVersion() == null) ? 0 : getVersion().hashCode());
        result = prime * result + ((getCreateTime() == null) ? 0 : getCreateTime().hashCode());
        result = prime * result + ((getUpdateTime() == null) ? 0 : getUpdateTime().hashCode());
        return result;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append(getClass().getSimpleName());
        sb.append(" [");
        sb.append("Hash = ").append(hashCode());
        sb.append(", id=").append(id);
        sb.append(", orderNo=").append(orderNo);
        sb.append(", customerId=").append(customerId);
        sb.append(", customerPhone=").append(customerPhone);
        sb.append(", orderSource=").append(orderSource);
        sb.append(", totalPrice=").append(totalPrice);
        sb.append(", payableAmount=").append(payableAmount);
        sb.append(", discountAmount=").append(discountAmount);
        sb.append(", dispatchStatus=").append(dispatchStatus);
        sb.append(", orderStatus=").append(orderStatus);
        sb.append(", payStatus=").append(payStatus);
        sb.append(", payChannel=").append(payChannel);
        sb.append(", payTime=").append(payTime);
        sb.append(", deliveryFee=").append(deliveryFee);
        sb.append(", driverId=").append(driverId);
        sb.append(", deliveryAddress=").append(deliveryAddress);
        sb.append(", addressId=").append(addressId);
        sb.append(", goodsWeight=").append(goodsWeight);
        sb.append(", couponId=").append(couponId);
        sb.append(", pointsUsed=").append(pointsUsed);
        sb.append(", expectedDeliveryTime=").append(expectedDeliveryTime);
        sb.append(", receiveTime=").append(receiveTime);
        sb.append(", remark=").append(remark);
        sb.append(", cancelReason=").append(cancelReason);
        sb.append(", version=").append(version);
        sb.append(", createTime=").append(createTime);
        sb.append(", updateTime=").append(updateTime);
        sb.append("]");
        return sb.toString();
    }
}
