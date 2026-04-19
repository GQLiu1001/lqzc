package com.lqzc.mcp.dto;

import java.util.List;

public record InventoryLogQueryResponse(
        Integer warehouseNum,
        String warehouseLabel,
        Long itemId,
        String model,
        Integer currentStock,
        Integer days,
        Long totalLogs,
        Integer inboundAmount,
        Integer outboundAmount,
        Integer transferAmount,
        List<InventoryLogItem> records
) {
}
