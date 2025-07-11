package com.lqzc.common.req;

import lombok.Data;

import java.math.BigDecimal;

/**
 * 库存商品修改请求类
 */
@Data
public class ItemsChangeReq {
    /**
     * 库存ID
     */
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
     * 规格
     */
    private String specification;
    
    /**
     * 表面处理（1=抛光 2=哑光 3=釉面 4=通体大理石 5=微晶石 6=岩板）
     */
    private Integer surface;

    private String picture;

    private BigDecimal sellingPrice;
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
     * 备注
     */
    private String remark;
}
