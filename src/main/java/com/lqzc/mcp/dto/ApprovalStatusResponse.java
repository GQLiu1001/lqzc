package com.lqzc.mcp.dto;

import java.util.List;

public record ApprovalStatusResponse(
        String approvalId,
        String status,
        String message,
        Integer warehouseNum,
        String warehouseLabel,
        Long itemId,
        String model,
        Integer requestedQuantity,
        Integer currentStock,
        String reason,
        Long requesterUserId,
        Long requesterRoleId,
        String requesterRoleKey,
        String idempotencyKey,
        List<String> allowedDecisions,
        String createdTime,
        String expireTime
) {
    public static ApprovalStatusResponse pending(
            String approvalId,
            Integer warehouseNum,
            String warehouseLabel,
            Long itemId,
            String model,
            Integer requestedQuantity,
            Integer currentStock,
            String reason,
            Long requesterUserId,
            Long requesterRoleId,
            String requesterRoleKey,
            String idempotencyKey,
            String createdTime,
            String expireTime
    ) {
        return new ApprovalStatusResponse(
                approvalId,
                "pending",
                "该操作已进入待审批状态",
                warehouseNum,
                warehouseLabel,
                itemId,
                model,
                requestedQuantity,
                currentStock,
                reason,
                requesterUserId,
                requesterRoleId,
                requesterRoleKey,
                idempotencyKey,
                List.of("approve", "reject"),
                createdTime,
                expireTime
        );
    }

    public static ApprovalStatusResponse notFound(String approvalId) {
        return new ApprovalStatusResponse(
                approvalId,
                "not_found",
                "未找到对应审批单",
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                List.of(),
                null,
                null
        );
    }
}
