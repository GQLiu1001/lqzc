package com.lqzc.mcp.dto;

import com.lqzc.common.domain.InventoryItem;
import com.lqzc.mcp.support.McpSupport;

import java.math.BigDecimal;

public record WarehouseInventoryResponse(
        Long itemId,
        Integer warehouseNum,
        String warehouseLabel,
        String model,
        String manufacturer,
        String specification,
        Integer category,
        String categoryLabel,
        Integer surface,
        String surfaceLabel,
        Integer totalAmount,
        Integer unitPerBox,
        BigDecimal sellingPrice,
        String remark,
        String updateTime
) {
    public static WarehouseInventoryResponse from(InventoryItem item) {
        return new WarehouseInventoryResponse(
                item.getId(),
                item.getWarehouseNum(),
                McpSupport.warehouseLabel(item.getWarehouseNum()),
                item.getModel(),
                item.getManufacturer(),
                item.getSpecification(),
                item.getCategory(),
                McpSupport.categoryLabel(item.getCategory()),
                item.getSurface(),
                McpSupport.surfaceLabel(item.getSurface()),
                item.getTotalAmount(),
                item.getUnitPerBox(),
                item.getSellingPrice(),
                item.getRemark(),
                McpSupport.formatDateTime(item.getUpdateTime())
        );
    }
}
