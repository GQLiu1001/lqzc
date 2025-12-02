package com.lqzc.common.resp;

import lombok.Data;
import java.math.BigDecimal;
import java.util.List;

/**
 * C端订单详情响应
 */
@Data
public class MallOrderDetailResp {
    private Long id;
    private String orderNo;
    private Long customerId;
    private String customerPhone;
    private Integer orderSource;
    private BigDecimal totalPrice;
    private BigDecimal payableAmount;
    private BigDecimal discountAmount;
    private Integer dispatchStatus;
    private Integer orderStatus;
    private Integer payStatus;
    private Integer payChannel;
    private String payTime;
    private BigDecimal deliveryFee;
    private BigDecimal goodsWeight;
    private Long couponId;
    private Integer pointsUsed;
    private String expectedDeliveryTime;
    private String receiveTime;
    private String remark;
    private String createTime;
    
    /** 收货地址 */
    private AddressInfo address;
    /** 订单项 */
    private List<OrderItemDetail> items;
    /** 状态历史 */
    private List<StatusHistoryItem> statusHistory;
    
    @Data
    public static class AddressInfo {
        private String receiverName;
        private String receiverPhone;
        private String province;
        private String city;
        private String district;
        private String detail;
    }
    
    @Data
    public static class OrderItemDetail {
        private Long id;
        private Long itemId;
        private String model;
        private String specification;
        private BigDecimal sellingPrice;
        private Integer amount;
        private BigDecimal subtotalPrice;
    }
    
    @Data
    public static class StatusHistoryItem {
        private Integer fromStatus;
        private Integer toStatus;
        private String remark;
        private String createTime;
    }
}
