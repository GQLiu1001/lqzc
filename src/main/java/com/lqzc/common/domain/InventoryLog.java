package com.lqzc.common.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.util.Date;
import lombok.Data;

/**
 * 库存操作日志表
 * @TableName inventory_log
 */
@TableName(value ="inventory_log")
@Data
public class InventoryLog {
    /**
     * 日志ID
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 库存项ID
     */
    private Long itemId;

    /**
     * 操作类型（1=入库 2=出库 3=调拨 4=冲正）
     */
    private Integer logType;

    /**
     * 数量变化 (正数表示增加, 负数表示减少)
     */
    private Integer amountChange;

    /**
     * 源仓库编码
     */
    private Integer sourceWarehouse;

    /**
     * 目标仓库编码
     */
    private Integer targetWarehouse;

    /**
     * 操作备注
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
        InventoryLog other = (InventoryLog) that;
        return (this.getId() == null ? other.getId() == null : this.getId().equals(other.getId()))
            && (this.getItemId() == null ? other.getItemId() == null : this.getItemId().equals(other.getItemId()))
            && (this.getLogType() == null ? other.getLogType() == null : this.getLogType().equals(other.getLogType()))
            && (this.getAmountChange() == null ? other.getAmountChange() == null : this.getAmountChange().equals(other.getAmountChange()))
            && (this.getSourceWarehouse() == null ? other.getSourceWarehouse() == null : this.getSourceWarehouse().equals(other.getSourceWarehouse()))
            && (this.getTargetWarehouse() == null ? other.getTargetWarehouse() == null : this.getTargetWarehouse().equals(other.getTargetWarehouse()))
            && (this.getRemark() == null ? other.getRemark() == null : this.getRemark().equals(other.getRemark()))
            && (this.getCreateTime() == null ? other.getCreateTime() == null : this.getCreateTime().equals(other.getCreateTime()))
            && (this.getUpdateTime() == null ? other.getUpdateTime() == null : this.getUpdateTime().equals(other.getUpdateTime()));
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int result = 1;
        result = prime * result + ((getId() == null) ? 0 : getId().hashCode());
        result = prime * result + ((getItemId() == null) ? 0 : getItemId().hashCode());
        result = prime * result + ((getLogType() == null) ? 0 : getLogType().hashCode());
        result = prime * result + ((getAmountChange() == null) ? 0 : getAmountChange().hashCode());
        result = prime * result + ((getSourceWarehouse() == null) ? 0 : getSourceWarehouse().hashCode());
        result = prime * result + ((getTargetWarehouse() == null) ? 0 : getTargetWarehouse().hashCode());
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
        sb.append(", itemId=").append(itemId);
        sb.append(", logType=").append(logType);
        sb.append(", amountChange=").append(amountChange);
        sb.append(", sourceWarehouse=").append(sourceWarehouse);
        sb.append(", targetWarehouse=").append(targetWarehouse);
        sb.append(", remark=").append(remark);
        sb.append(", createTime=").append(createTime);
        sb.append(", updateTime=").append(updateTime);
        sb.append("]");
        return sb.toString();
    }
}