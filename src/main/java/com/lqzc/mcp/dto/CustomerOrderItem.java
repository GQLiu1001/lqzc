package com.lqzc.mcp.dto;

import com.lqzc.mcp.support.McpSupport;

import java.math.BigDecimal;

public record CustomerOrderItem(
        String orderNo,
        Integer orderStatus,
        String orderStatusLabel,
        BigDecimal payableAmount,
        Integer itemCount,
        String createTime
) {
    public static String statusLabel(Integer status) {
        return McpSupport.orderStatusLabel(status, null, null);
    }

    public static String statusLabel(Integer status, Integer dispatchStatus, String cancelReason) {
        return McpSupport.orderStatusLabel(status, dispatchStatus, cancelReason);
    }
}
