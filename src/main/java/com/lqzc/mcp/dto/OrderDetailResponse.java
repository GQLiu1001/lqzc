package com.lqzc.mcp.dto;

import com.lqzc.mcp.support.McpSupport;

import java.math.BigDecimal;
import java.util.List;

public record OrderDetailResponse(
        String orderNo,
        Integer orderStatus,
        String orderStatusLabel,
        Integer payStatus,
        String payStatusLabel,
        Integer dispatchStatus,
        String dispatchStatusLabel,
        BigDecimal totalPrice,
        BigDecimal payableAmount,
        BigDecimal discountAmount,
        BigDecimal deliveryFee,
        String deliveryAddress,
        Integer pointsUsed,
        String payTime,
        String createTime,
        String receiveTime,
        String remark,
        List<ItemDetail> items
) {
    public record ItemDetail(
            String model,
            String specification,
            Integer amount,
            BigDecimal sellingPrice,
            BigDecimal subtotalPrice
    ) {}

    public static String orderStatusLabel(Integer status) {
        return McpSupport.orderStatusLabel(status, null, null);
    }

    public static String orderStatusLabel(Integer status, Integer dispatchStatus, String cancelReason) {
        return McpSupport.orderStatusLabel(status, dispatchStatus, cancelReason);
    }

    public static String payStatusLabel(Integer status) {
        return McpSupport.payStatusLabel(status);
    }

    public static String dispatchStatusLabel(Integer status) {
        return McpSupport.dispatchStatusLabel(status);
    }
}
