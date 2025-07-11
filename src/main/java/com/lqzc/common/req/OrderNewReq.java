package com.lqzc.common.req;

import lombok.Data;
import java.math.BigDecimal;
import java.util.List;

/**
 * 创建新订单请求类
 */
@Data
public class OrderNewReq {
    /**
     * 客户手机号
     */
    private String customerPhone;
    
    /**
     * 订单总金额
     */
    private BigDecimal totalPrice;
    
    /**
     * 订单项列表
     */
    private List<OrderNewItem> items;
    
    /**
     * 订单备注
     */
    private String remark;
    
    /**
     * 订单项内部类
     */
    @Data
    public static class OrderNewItem {
        /**
         * 库存商品ID
         */
        private Long itemId;
        
        /**
         * 产品型号
         */
        private String model;
        
        /**
         * 购买数量
         */
        private Integer amount;
        
        /**
         * 小计金额
         */
        private BigDecimal subtotalPrice;
    }
}
