package com.lqzc.common.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.Version;
import java.math.BigDecimal;
import java.util.Date;
import lombok.Data;

/**
 * 瓷砖库存表
 * @TableName inventory_item
 */
@TableName(value ="inventory_item")
@Data
public class InventoryItem {
    /**
     * 库存ID
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 产品型号
     */
    private String model;

    /**
     * 制造厂商
     */
    private String manufacturer;

    /**
     * 规格（如：600x600mm）
     */
    private String specification;

    /**
     * 表面处理（1=抛光 2=哑光 3=釉面 4=通体大理石 5=微晶石 6=岩板）
     */
    private Integer surface;

    /**
     * 分类（1=墙砖 2=地砖 3=胶 4=洁具）
     */
    private Integer category;

    /**
     * 仓库编码
     */
    private Integer warehouseNum;

    /**
     * 总个数
     */
    private Integer totalAmount;

    /**
     * 每箱个数
     */
    private Integer unitPerBox;

    /**
     * 图片
     */
    private String picture;

    /**
     * 销售单价（每片）
     */
    private BigDecimal sellingPrice;

    /**
     * 备注
     */
    private String remark;

    /**
     * 版本号（乐观锁）
     */
    @Version
    private Integer version;

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
        InventoryItem other = (InventoryItem) that;
        return (this.getId() == null ? other.getId() == null : this.getId().equals(other.getId()))
            && (this.getModel() == null ? other.getModel() == null : this.getModel().equals(other.getModel()))
            && (this.getManufacturer() == null ? other.getManufacturer() == null : this.getManufacturer().equals(other.getManufacturer()))
            && (this.getSpecification() == null ? other.getSpecification() == null : this.getSpecification().equals(other.getSpecification()))
            && (this.getSurface() == null ? other.getSurface() == null : this.getSurface().equals(other.getSurface()))
            && (this.getCategory() == null ? other.getCategory() == null : this.getCategory().equals(other.getCategory()))
            && (this.getWarehouseNum() == null ? other.getWarehouseNum() == null : this.getWarehouseNum().equals(other.getWarehouseNum()))
            && (this.getTotalAmount() == null ? other.getTotalAmount() == null : this.getTotalAmount().equals(other.getTotalAmount()))
            && (this.getUnitPerBox() == null ? other.getUnitPerBox() == null : this.getUnitPerBox().equals(other.getUnitPerBox()))
            && (this.getPicture() == null ? other.getPicture() == null : this.getPicture().equals(other.getPicture()))
            && (this.getSellingPrice() == null ? other.getSellingPrice() == null : this.getSellingPrice().equals(other.getSellingPrice()))
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
        result = prime * result + ((getModel() == null) ? 0 : getModel().hashCode());
        result = prime * result + ((getManufacturer() == null) ? 0 : getManufacturer().hashCode());
        result = prime * result + ((getSpecification() == null) ? 0 : getSpecification().hashCode());
        result = prime * result + ((getSurface() == null) ? 0 : getSurface().hashCode());
        result = prime * result + ((getCategory() == null) ? 0 : getCategory().hashCode());
        result = prime * result + ((getWarehouseNum() == null) ? 0 : getWarehouseNum().hashCode());
        result = prime * result + ((getTotalAmount() == null) ? 0 : getTotalAmount().hashCode());
        result = prime * result + ((getUnitPerBox() == null) ? 0 : getUnitPerBox().hashCode());
        result = prime * result + ((getPicture() == null) ? 0 : getPicture().hashCode());
        result = prime * result + ((getSellingPrice() == null) ? 0 : getSellingPrice().hashCode());
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
        sb.append(", model=").append(model);
        sb.append(", manufacturer=").append(manufacturer);
        sb.append(", specification=").append(specification);
        sb.append(", surface=").append(surface);
        sb.append(", category=").append(category);
        sb.append(", warehouseNum=").append(warehouseNum);
        sb.append(", totalAmount=").append(totalAmount);
        sb.append(", unitPerBox=").append(unitPerBox);
        sb.append(", picture=").append(picture);
        sb.append(", sellingPrice=").append(sellingPrice);
        sb.append(", remark=").append(remark);
        sb.append(", version=").append(version);
        sb.append(", createTime=").append(createTime);
        sb.append(", updateTime=").append(updateTime);
        sb.append("]");
        return sb.toString();
    }
}