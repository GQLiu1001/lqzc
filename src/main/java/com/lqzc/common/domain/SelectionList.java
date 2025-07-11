package com.lqzc.common.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.util.Date;
import lombok.Data;

/**
 * 选品单主表
 * @TableName selection_list
 */
@TableName(value ="selection_list")
@Data
public class SelectionList {
    /**
     * 选品单ID
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 选品单编号 (例如：XPD20240725001)
     */
    private String selectionNo;

    /**
     * 客户手机号 (可选填)
     */
    private String customerPhone;

    /**
     * 处理状态 (0=待跟进, 1=已联系, 2=已到店, 3=已失效)
     */
    private Integer status;

    /**
     * 客户意向派送地址 (可选填)
     */
    private String deliveryAddress;

    /**
     * 客户备注
     */
    private String remark;

    /**
     * 创建时间
     */
    private Date createTime;

    /**
     * 更新时间
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
        SelectionList other = (SelectionList) that;
        return (this.getId() == null ? other.getId() == null : this.getId().equals(other.getId()))
            && (this.getSelectionNo() == null ? other.getSelectionNo() == null : this.getSelectionNo().equals(other.getSelectionNo()))
            && (this.getCustomerPhone() == null ? other.getCustomerPhone() == null : this.getCustomerPhone().equals(other.getCustomerPhone()))
            && (this.getStatus() == null ? other.getStatus() == null : this.getStatus().equals(other.getStatus()))
            && (this.getDeliveryAddress() == null ? other.getDeliveryAddress() == null : this.getDeliveryAddress().equals(other.getDeliveryAddress()))
            && (this.getRemark() == null ? other.getRemark() == null : this.getRemark().equals(other.getRemark()))
            && (this.getCreateTime() == null ? other.getCreateTime() == null : this.getCreateTime().equals(other.getCreateTime()))
            && (this.getUpdateTime() == null ? other.getUpdateTime() == null : this.getUpdateTime().equals(other.getUpdateTime()));
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int result = 1;
        result = prime * result + ((getId() == null) ? 0 : getId().hashCode());
        result = prime * result + ((getSelectionNo() == null) ? 0 : getSelectionNo().hashCode());
        result = prime * result + ((getCustomerPhone() == null) ? 0 : getCustomerPhone().hashCode());
        result = prime * result + ((getStatus() == null) ? 0 : getStatus().hashCode());
        result = prime * result + ((getDeliveryAddress() == null) ? 0 : getDeliveryAddress().hashCode());
        result = prime * result + ((getRemark() == null) ? 0 : getRemark().hashCode());
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
        sb.append(", selectionNo=").append(selectionNo);
        sb.append(", customerPhone=").append(customerPhone);
        sb.append(", status=").append(status);
        sb.append(", deliveryAddress=").append(deliveryAddress);
        sb.append(", remark=").append(remark);
        sb.append(", createTime=").append(createTime);
        sb.append(", updateTime=").append(updateTime);
        sb.append("]");
        return sb.toString();
    }
}