package com.lqzc.common.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.util.Date;
import lombok.Data;

/**
 * 客户积分账户
 * @TableName loyalty_points_account
 */
@TableName(value ="loyalty_points_account")
@Data
public class LoyaltyPointsAccount {
    /**
     * 主键
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 客户ID
     */
    private Long customerId;

    /**
     * 当前可用积分
     */
    private Integer balance;

    /**
     * 累计获取
     */
    private Integer totalEarned;

    /**
     * 累计消耗
     */
    private Integer totalSpent;

    /**
     * 冻结积分
     */
    private Integer frozen;

    /**
     * 
     */
    private Date createTime;

    /**
     * 
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
        LoyaltyPointsAccount other = (LoyaltyPointsAccount) that;
        return (this.getId() == null ? other.getId() == null : this.getId().equals(other.getId()))
            && (this.getCustomerId() == null ? other.getCustomerId() == null : this.getCustomerId().equals(other.getCustomerId()))
            && (this.getBalance() == null ? other.getBalance() == null : this.getBalance().equals(other.getBalance()))
            && (this.getTotalEarned() == null ? other.getTotalEarned() == null : this.getTotalEarned().equals(other.getTotalEarned()))
            && (this.getTotalSpent() == null ? other.getTotalSpent() == null : this.getTotalSpent().equals(other.getTotalSpent()))
            && (this.getFrozen() == null ? other.getFrozen() == null : this.getFrozen().equals(other.getFrozen()))
            && (this.getCreateTime() == null ? other.getCreateTime() == null : this.getCreateTime().equals(other.getCreateTime()))
            && (this.getUpdateTime() == null ? other.getUpdateTime() == null : this.getUpdateTime().equals(other.getUpdateTime()));
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int result = 1;
        result = prime * result + ((getId() == null) ? 0 : getId().hashCode());
        result = prime * result + ((getCustomerId() == null) ? 0 : getCustomerId().hashCode());
        result = prime * result + ((getBalance() == null) ? 0 : getBalance().hashCode());
        result = prime * result + ((getTotalEarned() == null) ? 0 : getTotalEarned().hashCode());
        result = prime * result + ((getTotalSpent() == null) ? 0 : getTotalSpent().hashCode());
        result = prime * result + ((getFrozen() == null) ? 0 : getFrozen().hashCode());
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
        sb.append(", customerId=").append(customerId);
        sb.append(", balance=").append(balance);
        sb.append(", totalEarned=").append(totalEarned);
        sb.append(", totalSpent=").append(totalSpent);
        sb.append(", frozen=").append(frozen);
        sb.append(", createTime=").append(createTime);
        sb.append(", updateTime=").append(updateTime);
        sb.append("]");
        return sb.toString();
    }
}
