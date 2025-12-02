package com.lqzc.common.resp;

import java.math.BigDecimal;
import java.util.List;
import lombok.Data;

@Data
public class OrderListItemResp {
    /** 订单编号 */
    private String orderNo;
    /** 订单状态 */
    private Integer status;
    /** 应付金额 */
    private BigDecimal payableAmount;
    /** 商品摘要列表 */
    private List<OrderItemSummary> items;

    @Data
    public static class OrderItemSummary {
        /** 型号 */
        private String model;
        /** 图片 */
        private String picture;
        /** 数量 */
        private Integer amount;
    }
}
