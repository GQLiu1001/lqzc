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
     * 客户手机号
     */
    private String customerPhone;

    /**
     * 订单总金额
     */
    private BigDecimal totalPrice;

    /**
     * 订单派送状态：0=待派送 1=待接单 2=派送中 3=已完成
     */
    private Integer dispatchStatus;

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
     * 订单备注
     */
    private String remark;

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
            && (this.getCustomerPhone() == null ? other.getCustomerPhone() == null : this.getCustomerPhone().equals(other.getCustomerPhone()))
            && (this.getTotalPrice() == null ? other.getTotalPrice() == null : this.getTotalPrice().equals(other.getTotalPrice()))
            && (this.getDispatchStatus() == null ? other.getDispatchStatus() == null : this.getDispatchStatus().equals(other.getDispatchStatus()))
            && (this.getDriverId() == null ? other.getDriverId() == null : this.getDriverId().equals(other.getDriverId()))
            && (this.getDeliveryAddress() == null ? other.getDeliveryAddress() == null : this.getDeliveryAddress().equals(other.getDeliveryAddress()))
            && (this.getDeliveryFee() == null ? other.getDeliveryFee() == null : this.getDeliveryFee().equals(other.getDeliveryFee()))
            && (this.getGoodsWeight() == null ? other.getGoodsWeight() == null : this.getGoodsWeight().equals(other.getGoodsWeight()))
            && (this.getRemark() == null ? other.getRemark() == null : this.getRemark().equals(other.getRemark()))
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
        result = prime * result + ((getCustomerPhone() == null) ? 0 : getCustomerPhone().hashCode());
        result = prime * result + ((getTotalPrice() == null) ? 0 : getTotalPrice().hashCode());
        result = prime * result + ((getDispatchStatus() == null) ? 0 : getDispatchStatus().hashCode());
        result = prime * result + ((getDriverId() == null) ? 0 : getDriverId().hashCode());
        result = prime * result + ((getDeliveryAddress() == null) ? 0 : getDeliveryAddress().hashCode());
        result = prime * result + ((getDeliveryFee() == null) ? 0 : getDeliveryFee().hashCode());
        result = prime * result + ((getGoodsWeight() == null) ? 0 : getGoodsWeight().hashCode());
        result = prime * result + ((getRemark() == null) ? 0 : getRemark().hashCode());
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
        sb.append(", customerPhone=").append(customerPhone);
        sb.append(", totalPrice=").append(totalPrice);
        sb.append(", dispatchStatus=").append(dispatchStatus);
        sb.append(", driverId=").append(driverId);
        sb.append(", deliveryAddress=").append(deliveryAddress);
        sb.append(", deliveryFee=").append(deliveryFee);
        sb.append(", goodsWeight=").append(goodsWeight);
        sb.append(", remark=").append(remark);
        sb.append(", version=").append(version);
        sb.append(", createTime=").append(createTime);
        sb.append(", updateTime=").append(updateTime);
        sb.append("]");
        return sb.toString();
    }
}