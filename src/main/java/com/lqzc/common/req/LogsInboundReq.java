package com.lqzc.common.req;

import lombok.Data;

import java.math.BigDecimal;

/**
 * 创建入库记录请求类
 */
@Data
public class LogsInboundReq {
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
     * 仓库编码
     */
    private Integer warehouseNum;
    
    /**
     * 分类（1=墙砖 2=地砖 3=胶 4=洁具）
     */
    private Integer category;
    
    /**
     * 表面处理（1=抛光 2=哑光 3=釉面 4=通体大理石 5=微晶石 6=岩板）
     */
    private Integer surface;
    
    /**
     * 总个数
     */
    private Integer totalAmount;

    private String picture;

    private BigDecimal sellingPrice;

    /**
     * 每箱个数
     */
    private Integer unitPerBox;
    
    /**
     * 备注
     */
    private String remark;
}
