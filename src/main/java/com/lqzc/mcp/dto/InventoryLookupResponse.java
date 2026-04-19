package com.lqzc.mcp.dto;

import com.lqzc.common.domain.InventoryItem;
import com.lqzc.mcp.support.McpSupport;

import java.math.BigDecimal;

public record InventoryLookupResponse(
        Long id,
        String model,
        String manufacturer,
        String specification,
        Integer category,
        String categoryLabel,
        Integer surface,
        String surfaceLabel,
        Integer warehouseCode,
        String warehouseLabel,
        Integer totalAmount,
        Integer unitPerBox,
        BigDecimal sellingPrice,
        String remark
) {
    public static InventoryLookupResponse from(InventoryItem item) {
        return from(
                item,
                McpSupport.categoryLabel(item.getCategory()),
                McpSupport.surfaceLabel(item.getSurface())
        );
    }

    public static InventoryLookupResponse from(InventoryItem item, String categoryLabel, String surfaceLabel) {
        return new InventoryLookupResponse(
                item.getId(),
                item.getModel(),
                item.getManufacturer(),
                item.getSpecification(),
                item.getCategory(),
                categoryLabel,
                item.getSurface(),
                surfaceLabel,
                item.getWarehouseNum(),
                McpSupport.warehouseLabel(item.getWarehouseNum()),
                item.getTotalAmount(),
                item.getUnitPerBox(),
                item.getSellingPrice(),
                item.getRemark()
        );
    }
}
