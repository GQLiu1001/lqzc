package com.lqzc.common.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.util.Date;
import lombok.Data;

/**
 * 选品单明细表
 * @TableName selection_item
 */
@TableName(value ="selection_item")
@Data
public class SelectionItem {
    /**
     * 选品明细ID
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 所属选品单ID
     */
    private Long selectionId;

    /**
     * 产品型号 (不使用item_id，因为库存项可能会被删除)
     */
    private String itemModel;

    /**
     * 规格快照
     */
    private String itemSpecification;

    /**
     * 当时单价快照
     */
    private BigDecimal itemSellingPrice;

    /**
     * 意向数量
     */
    private Integer amount;

    /**
     * 创建时间
     */
    private Date createTime;

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
        SelectionItem other = (SelectionItem) that;
        return (this.getId() == null ? other.getId() == null : this.getId().equals(other.getId()))
            && (this.getSelectionId() == null ? other.getSelectionId() == null : this.getSelectionId().equals(other.getSelectionId()))
            && (this.getItemModel() == null ? other.getItemModel() == null : this.getItemModel().equals(other.getItemModel()))
            && (this.getItemSpecification() == null ? other.getItemSpecification() == null : this.getItemSpecification().equals(other.getItemSpecification()))
            && (this.getItemSellingPrice() == null ? other.getItemSellingPrice() == null : this.getItemSellingPrice().equals(other.getItemSellingPrice()))
            && (this.getAmount() == null ? other.getAmount() == null : this.getAmount().equals(other.getAmount()))
            && (this.getCreateTime() == null ? other.getCreateTime() == null : this.getCreateTime().equals(other.getCreateTime()));
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int result = 1;
        result = prime * result + ((getId() == null) ? 0 : getId().hashCode());
        result = prime * result + ((getSelectionId() == null) ? 0 : getSelectionId().hashCode());
        result = prime * result + ((getItemModel() == null) ? 0 : getItemModel().hashCode());
        result = prime * result + ((getItemSpecification() == null) ? 0 : getItemSpecification().hashCode());
        result = prime * result + ((getItemSellingPrice() == null) ? 0 : getItemSellingPrice().hashCode());
        result = prime * result + ((getAmount() == null) ? 0 : getAmount().hashCode());
        result = prime * result + ((getCreateTime() == null) ? 0 : getCreateTime().hashCode());
        return result;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append(getClass().getSimpleName());
        sb.append(" [");
        sb.append("Hash = ").append(hashCode());
        sb.append(", id=").append(id);
        sb.append(", selectionId=").append(selectionId);
        sb.append(", itemModel=").append(itemModel);
        sb.append(", itemSpecification=").append(itemSpecification);
        sb.append(", itemSellingPrice=").append(itemSellingPrice);
        sb.append(", amount=").append(amount);
        sb.append(", createTime=").append(createTime);
        sb.append("]");
        return sb.toString();
    }
}