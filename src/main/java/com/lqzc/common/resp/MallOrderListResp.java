package com.lqzc.common.resp;

import lombok.Data;
import java.math.BigDecimal;
import java.util.List;

/**
 * C端订单列表响应
 */
@Data
public class MallOrderListResp {
    /** 订单号 */
    private String orderNo;
    /** 订单状态 */
    private Integer status;
    /** 应付金额 */
    private BigDecimal payableAmount;
    /** 创建时间 */
    private String createTime;
    /** 订单项 */
    private List<OrderItemInfo> items;
    
    @Data
    public static class OrderItemInfo {
        /** 商品型号 */
        private String model;
        /** 商品图片 */
        private String picture;
        /** 数量 */
        private Integer amount;
    }
}

