package com.lqzc.common.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.util.Date;
import lombok.Data;

/**
 * 优惠券模板
 * @TableName coupon_template
 */
@TableName(value ="coupon_template")
@Data
public class CouponTemplate {
    /**
     * 模板ID
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 优惠券标题
     */
    private String title;

    /**
     * 1=满减 2=折扣 3=现金券
     */
    private Integer type;

    /**
     * 使用门槛金额
     */
    private BigDecimal thresholdAmount;

    /**
     * 立减金额
     */
    private BigDecimal discountAmount;

    /**
     * 折扣（0.90代表9折）
     */
    private BigDecimal discountRate;

    /**
     * 折扣封顶
     */
    private BigDecimal maxDiscount;

    /**
     * 有效期开始
     */
    private Date validFrom;

    /**
     * 有效期结束
     */
    private Date validTo;

    /**
     * 投放量
     */
    private Integer totalIssued;

    /**
     * 每人限领
     */
    private Integer perUserLimit;

    /**
     * 状态：1启用 0停用
     */
    private Integer status;

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
        CouponTemplate other = (CouponTemplate) that;
        return (this.getId() == null ? other.getId() == null : this.getId().equals(other.getId()))
            && (this.getTitle() == null ? other.getTitle() == null : this.getTitle().equals(other.getTitle()))
            && (this.getType() == null ? other.getType() == null : this.getType().equals(other.getType()))
            && (this.getThresholdAmount() == null ? other.getThresholdAmount() == null : this.getThresholdAmount().equals(other.getThresholdAmount()))
            && (this.getDiscountAmount() == null ? other.getDiscountAmount() == null : this.getDiscountAmount().equals(other.getDiscountAmount()))
            && (this.getDiscountRate() == null ? other.getDiscountRate() == null : this.getDiscountRate().equals(other.getDiscountRate()))
            && (this.getMaxDiscount() == null ? other.getMaxDiscount() == null : this.getMaxDiscount().equals(other.getMaxDiscount()))
            && (this.getValidFrom() == null ? other.getValidFrom() == null : this.getValidFrom().equals(other.getValidFrom()))
            && (this.getValidTo() == null ? other.getValidTo() == null : this.getValidTo().equals(other.getValidTo()))
            && (this.getTotalIssued() == null ? other.getTotalIssued() == null : this.getTotalIssued().equals(other.getTotalIssued()))
            && (this.getPerUserLimit() == null ? other.getPerUserLimit() == null : this.getPerUserLimit().equals(other.getPerUserLimit()))
            && (this.getStatus() == null ? other.getStatus() == null : this.getStatus().equals(other.getStatus()))
            && (this.getCreateTime() == null ? other.getCreateTime() == null : this.getCreateTime().equals(other.getCreateTime()))
            && (this.getUpdateTime() == null ? other.getUpdateTime() == null : this.getUpdateTime().equals(other.getUpdateTime()));
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int result = 1;
        result = prime * result + ((getId() == null) ? 0 : getId().hashCode());
        result = prime * result + ((getTitle() == null) ? 0 : getTitle().hashCode());
        result = prime * result + ((getType() == null) ? 0 : getType().hashCode());
        result = prime * result + ((getThresholdAmount() == null) ? 0 : getThresholdAmount().hashCode());
        result = prime * result + ((getDiscountAmount() == null) ? 0 : getDiscountAmount().hashCode());
        result = prime * result + ((getDiscountRate() == null) ? 0 : getDiscountRate().hashCode());
        result = prime * result + ((getMaxDiscount() == null) ? 0 : getMaxDiscount().hashCode());
        result = prime * result + ((getValidFrom() == null) ? 0 : getValidFrom().hashCode());
        result = prime * result + ((getValidTo() == null) ? 0 : getValidTo().hashCode());
        result = prime * result + ((getTotalIssued() == null) ? 0 : getTotalIssued().hashCode());
        result = prime * result + ((getPerUserLimit() == null) ? 0 : getPerUserLimit().hashCode());
        result = prime * result + ((getStatus() == null) ? 0 : getStatus().hashCode());
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
        sb.append(", title=").append(title);
        sb.append(", type=").append(type);
        sb.append(", thresholdAmount=").append(thresholdAmount);
        sb.append(", discountAmount=").append(discountAmount);
        sb.append(", discountRate=").append(discountRate);
        sb.append(", maxDiscount=").append(maxDiscount);
        sb.append(", validFrom=").append(validFrom);
        sb.append(", validTo=").append(validTo);
        sb.append(", totalIssued=").append(totalIssued);
        sb.append(", perUserLimit=").append(perUserLimit);
        sb.append(", status=").append(status);
        sb.append(", createTime=").append(createTime);
        sb.append(", updateTime=").append(updateTime);
        sb.append("]");
        return sb.toString();
    }
}
