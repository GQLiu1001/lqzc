package com.lqzc.mcp.dto;

import com.lqzc.mcp.support.McpSupport;

public record InventoryLogItem(
        Long id,
        Long itemId,
        Integer logType,
        String logTypeLabel,
        Integer amountChange,
        Integer sourceWarehouse,
        Integer targetWarehouse,
        String remark,
        String createTime
) {
    public static String logTypeLabel(Integer logType) {
        return McpSupport.inventoryLogTypeLabel(logType);
    }
}
