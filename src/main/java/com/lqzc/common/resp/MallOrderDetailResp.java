package com.lqzc.common.resp;

import java.math.BigDecimal;
import java.util.List;
import lombok.Data;

@Data
public class MallOrderDetailResp {
    /** 订单ID */
    private Long id;
    /** 订单编号 */
    private String orderNo;
    /** 客户ID */
    private Long customerId;
    /** 客户手机号 */
    private String customerPhone;
    /** 订单来源 */
    private Integer orderSource;
    /** 总金额 */
    private BigDecimal totalPrice;
    /** 应付金额 */
    private BigDecimal payableAmount;
    /** 优惠合计 */
    private BigDecimal discountAmount;
    /** 派送状态 */
    private Integer dispatchStatus;
    /** 订单状态 */
    private Integer orderStatus;
    /** 支付状态 */
    private Integer payStatus;
    /** 支付渠道 */
    private Integer payChannel;
    /** 支付时间 */
    private String payTime;
    /** 配送费用 */
    private BigDecimal deliveryFee;
    /** 货物重量 */
    private BigDecimal goodsWeight;
    /** 优惠券ID */
    private Long couponId;
    /** 使用积分 */
    private Integer pointsUsed;
    /** 期望送达时间 */
    private String expectedDeliveryTime;
    /** 收货时间 */
    private String receiveTime;
    /** 备注 */
    private String remark;
    /** 创建时间 */
    private String createTime;
    /** 地址快照 */
    private AddressSnapshot address;
    /** 商品列表 */
    private List<Item> items;
    /** 状态流转 */
    private List<StatusHistory> statusHistory;

    @Data
    public static class AddressSnapshot {
        /** 收货人 */
        private String receiverName;
        /** 收货人手机号 */
        private String receiverPhone;
        /** 省 */
        private String province;
        /** 市 */
        private String city;
        /** 区县 */
        private String district;
        /** 详细地址 */
        private String detail;
    }

    @Data
    public static class Item {
        /** 订单项ID */
        private Long id;
        /** 商品ID */
        private Long itemId;
        /** 型号 */
        private String model;
        /** 图片 */
        private String picture;
        /** 规格 */
        private String specification;
        /** 销售价 */
        private BigDecimal sellingPrice;
        /** 数量 */
        private Integer amount;
        /** 小计金额 */
        private BigDecimal subtotalPrice;
    }

    @Data
    public static class StatusHistory {
        /** 变更前状态 */
        private Integer fromStatus;
        /** 变更后状态 */
        private Integer toStatus;
        /** 备注 */
        private String remark;
        /** 创建时间 */
        private String createTime;
    }
}
