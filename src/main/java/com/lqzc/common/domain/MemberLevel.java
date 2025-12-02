package com.lqzc.common.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.util.Date;
import lombok.Data;

/**
 * 会员等级配置
 * @TableName member_level
 */
@TableName(value ="member_level")
@Data
public class MemberLevel {
    /**
     * 主键
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 等级：1=普通 2=银卡 3=金卡 4=黑金
     */
    private Integer level;

    /**
     * 等级名称
     */
    private String name;

    /**
     * 升级起始积分
     */
    private Integer minPoints;

    /**
     * 升级终止积分（闭区间）
     */
    private Integer maxPoints;

    /**
     * 权益描述
     */
    private String benefits;

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
        MemberLevel other = (MemberLevel) that;
        return (this.getId() == null ? other.getId() == null : this.getId().equals(other.getId()))
            && (this.getLevel() == null ? other.getLevel() == null : this.getLevel().equals(other.getLevel()))
            && (this.getName() == null ? other.getName() == null : this.getName().equals(other.getName()))
            && (this.getMinPoints() == null ? other.getMinPoints() == null : this.getMinPoints().equals(other.getMinPoints()))
            && (this.getMaxPoints() == null ? other.getMaxPoints() == null : this.getMaxPoints().equals(other.getMaxPoints()))
            && (this.getBenefits() == null ? other.getBenefits() == null : this.getBenefits().equals(other.getBenefits()))
            && (this.getCreateTime() == null ? other.getCreateTime() == null : this.getCreateTime().equals(other.getCreateTime()))
            && (this.getUpdateTime() == null ? other.getUpdateTime() == null : this.getUpdateTime().equals(other.getUpdateTime()));
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int result = 1;
        result = prime * result + ((getId() == null) ? 0 : getId().hashCode());
        result = prime * result + ((getLevel() == null) ? 0 : getLevel().hashCode());
        result = prime * result + ((getName() == null) ? 0 : getName().hashCode());
        result = prime * result + ((getMinPoints() == null) ? 0 : getMinPoints().hashCode());
        result = prime * result + ((getMaxPoints() == null) ? 0 : getMaxPoints().hashCode());
        result = prime * result + ((getBenefits() == null) ? 0 : getBenefits().hashCode());
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
        sb.append(", level=").append(level);
        sb.append(", name=").append(name);
        sb.append(", minPoints=").append(minPoints);
        sb.append(", maxPoints=").append(maxPoints);
        sb.append(", benefits=").append(benefits);
        sb.append(", createTime=").append(createTime);
        sb.append(", updateTime=").append(updateTime);
        sb.append("]");
        return sb.toString();
    }
}
