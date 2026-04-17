package com.lqzc.mcp.tool;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.lqzc.common.constant.LogConstant;
import com.lqzc.common.domain.InventoryItem;
import com.lqzc.common.domain.InventoryLog;
import com.lqzc.common.domain.Role;
import com.lqzc.mcp.dto.ApprovalStatusResponse;
import com.lqzc.mcp.dto.InventoryLogItem;
import com.lqzc.mcp.dto.InventoryLogQueryResponse;
import com.lqzc.mcp.dto.WarehouseInventoryResponse;
import com.lqzc.mcp.support.McpSupport;
import com.lqzc.service.InventoryItemService;
import com.lqzc.service.InventoryLogService;
import com.lqzc.service.RoleService;
import lombok.RequiredArgsConstructor;
import org.springaicommunity.mcp.annotation.McpTool;
import org.springaicommunity.mcp.annotation.McpToolParam;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class WarehouseMcpTools {

    private static final int DEFAULT_LOG_DAYS = 7;
    private static final int MAX_LOG_DAYS = 90;
    private static final int DEFAULT_LOG_LIMIT = 20;
    private static final int MAX_LOG_LIMIT = 100;
    private static final long APPROVAL_TTL_DAYS = 3L;
    private static final String APPROVAL_KEY_PREFIX = "mcp:approval:status:";
    private static final String APPROVAL_IDEMPOTENCY_PREFIX = "mcp:approval:idempotency:";

    private final InventoryItemService inventoryItemService;
    private final InventoryLogService inventoryLogService;
    private final RoleService roleService;
    private final StringRedisTemplate stringRedisTemplate;
    private final ObjectMapper objectMapper;

    @McpTool(
            name = "getWarehouseInventory",
            description = "根据仓库编号和库存项ID或商品型号查询仓库库存快照，返回当前库存、规格、价格与更新时间"
    )
    public WarehouseInventoryResponse getWarehouseInventory(
            @McpToolParam(description = "仓库编号，例如 2", required = true)
            Integer warehouseNum,
            @McpToolParam(description = "库存项ID，与 model 二选一", required = false)
            Long itemId,
            @McpToolParam(description = "商品型号，与 itemId 二选一", required = false)
            String model
    ) {
        InventoryItem item = findInventoryItem(warehouseNum, itemId, model);
        return WarehouseInventoryResponse.from(item);
    }

    @McpTool(
            name = "getInventoryLog",
            description = "查询指定仓库某库存项近 N 天库存流水，返回当前库存、入出库汇总和流水明细"
    )
    public InventoryLogQueryResponse getInventoryLog(
            @McpToolParam(description = "仓库编号，例如 2", required = true)
            Integer warehouseNum,
            @McpToolParam(description = "库存项ID", required = true)
            Long itemId,
            @McpToolParam(description = "查询最近多少天，默认 7，最大 90", required = false)
            Integer days,
            @McpToolParam(description = "返回日志条数，默认 20，最大 100", required = false)
            Integer limit
    ) {
        InventoryItem item = findInventoryItem(warehouseNum, itemId, null);
        int lookbackDays = normalizeDays(days);
        int safeLimit = normalizeLogLimit(limit);
        Date startTime = Date.from(Instant.now().minus(lookbackDays, ChronoUnit.DAYS));

        List<InventoryLog> matchedLogs = inventoryLogService.list(
                        new LambdaQueryWrapper<InventoryLog>()
                                .eq(InventoryLog::getItemId, item.getId())
                                .ge(InventoryLog::getCreateTime, startTime)
                                .orderByDesc(InventoryLog::getCreateTime)
                ).stream()
                .filter(log -> belongsToWarehouse(log, warehouseNum))
                .toList();

        List<InventoryLogItem> records = matchedLogs.stream()
                .limit(safeLimit)
                .map(log -> new InventoryLogItem(
                        log.getId(),
                        log.getItemId(),
                        log.getLogType(),
                        InventoryLogItem.logTypeLabel(log.getLogType()),
                        log.getAmountChange(),
                        log.getSourceWarehouse(),
                        log.getTargetWarehouse(),
                        log.getRemark(),
                        McpSupport.formatDateTime(log.getCreateTime())
                ))
                .toList();

        return new InventoryLogQueryResponse(
                warehouseNum,
                McpSupport.warehouseLabel(warehouseNum),
                item.getId(),
                item.getModel(),
                item.getTotalAmount(),
                lookbackDays,
                (long) matchedLogs.size(),
                sumAmount(matchedLogs, LogConstant.INBOUND),
                sumAmount(matchedLogs, LogConstant.OUTBOUND),
                sumAmount(matchedLogs, LogConstant.TRANSFER),
                records
        );
    }

    @McpTool(
            name = "submitOutboundApply",
            description = "提交仓库出库申请并返回审批单状态，要求传入内部注入的操作者 userId、roleId 和幂等键"
    )
    public ApprovalStatusResponse submitOutboundApply(
            @McpToolParam(description = "仓库编号，例如 2", required = true)
            Integer warehouseNum,
            @McpToolParam(description = "库存项ID", required = true)
            Long itemId,
            @McpToolParam(description = "申请出库数量，必须大于 0", required = true)
            Integer quantity,
            @McpToolParam(description = "出库原因，可选", required = false)
            String reason,
            @McpToolParam(description = "操作者用户ID，由 FastAPI 运行时上下文注入", required = true)
            Long operatorUserId,
            @McpToolParam(description = "操作者角色ID，由 FastAPI 运行时上下文注入", required = true)
            Long roleId,
            @McpToolParam(description = "幂等键，由 FastAPI 侧按 sessionId/tool/business_key 生成", required = true)
            String idempotencyKey
    ) {
        validateWarehouseNum(warehouseNum);
        if (itemId == null || itemId <= 0) {
            throw new IllegalArgumentException("itemId 非法");
        }
        if (quantity == null || quantity <= 0) {
            throw new IllegalArgumentException("quantity 必须大于 0");
        }
        if (operatorUserId == null || operatorUserId <= 0) {
            throw new IllegalArgumentException("operatorUserId 非法");
        }
        if (roleId == null || roleId <= 0) {
            throw new IllegalArgumentException("roleId 非法");
        }
        String normalizedIdempotencyKey = requireText(idempotencyKey, "idempotencyKey");

        String existedApprovalId = stringRedisTemplate.opsForValue()
                .get(APPROVAL_IDEMPOTENCY_PREFIX + normalizedIdempotencyKey);
        if (existedApprovalId != null && !existedApprovalId.isBlank()) {
            return getApprovalStatus(existedApprovalId);
        }

        Role role = roleService.getById(roleId);
        if (!isAllowedApprovalRole(role, roleId)) {
            throw new IllegalStateException("当前角色无权发起仓库出库审批");
        }

        InventoryItem item = findInventoryItem(warehouseNum, itemId, null);
        if (item.getTotalAmount() == null || item.getTotalAmount() < quantity) {
            throw new IllegalStateException("库存不足，无法提交出库申请");
        }

        String approvalId = generateApprovalId();
        Date createdAt = new Date();
        Date expireAt = Date.from(createdAt.toInstant().plus(APPROVAL_TTL_DAYS, ChronoUnit.DAYS));
        ApprovalStatusResponse response = ApprovalStatusResponse.pending(
                approvalId,
                warehouseNum,
                McpSupport.warehouseLabel(warehouseNum),
                item.getId(),
                item.getModel(),
                quantity,
                item.getTotalAmount(),
                McpSupport.normalizeBlank(reason),
                operatorUserId,
                roleId,
                resolveRoleKey(role, roleId),
                normalizedIdempotencyKey,
                McpSupport.formatDateTime(createdAt),
                McpSupport.formatDateTime(expireAt)
        );

        saveApprovalStatus(response);
        stringRedisTemplate.opsForValue().set(
                APPROVAL_IDEMPOTENCY_PREFIX + normalizedIdempotencyKey,
                approvalId,
                APPROVAL_TTL_DAYS,
                TimeUnit.DAYS
        );
        return response;
    }

    @McpTool(
            name = "getApprovalStatus",
            description = "根据审批单号查询当前审批状态，适用于审批中断后的恢复查询"
    )
    public ApprovalStatusResponse getApprovalStatus(
            @McpToolParam(description = "审批单号，例如 AP202604170001", required = true)
            String approvalId
    ) {
        String normalizedApprovalId = requireText(approvalId, "approvalId");
        String rawValue = stringRedisTemplate.opsForValue().get(APPROVAL_KEY_PREFIX + normalizedApprovalId);
        if (rawValue == null || rawValue.isBlank()) {
            return ApprovalStatusResponse.notFound(normalizedApprovalId);
        }
        try {
            return objectMapper.readValue(rawValue, ApprovalStatusResponse.class);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("审批状态反序列化失败", e);
        }
    }

    private InventoryItem findInventoryItem(Integer warehouseNum, Long itemId, String model) {
        validateWarehouseNum(warehouseNum);
        String normalizedModel = McpSupport.normalizeBlank(model);
        if ((itemId == null || itemId <= 0) && normalizedModel == null) {
            throw new IllegalArgumentException("itemId 和 model 至少需要传一个");
        }

        LambdaQueryWrapper<InventoryItem> wrapper = new LambdaQueryWrapper<InventoryItem>()
                .eq(InventoryItem::getWarehouseNum, warehouseNum);
        if (itemId != null && itemId > 0) {
            wrapper.eq(InventoryItem::getId, itemId);
        } else {
            wrapper.eq(InventoryItem::getModel, normalizedModel);
        }

        InventoryItem item = inventoryItemService.getOne(wrapper);
        if (item == null) {
            throw new IllegalStateException("未找到对应仓库库存项");
        }
        return item;
    }

    private void saveApprovalStatus(ApprovalStatusResponse response) {
        try {
            stringRedisTemplate.opsForValue().set(
                    APPROVAL_KEY_PREFIX + response.approvalId(),
                    objectMapper.writeValueAsString(response),
                    APPROVAL_TTL_DAYS,
                    TimeUnit.DAYS
            );
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("审批状态序列化失败", e);
        }
    }

    private static boolean belongsToWarehouse(InventoryLog log, Integer warehouseNum) {
        return Objects.equals(log.getSourceWarehouse(), warehouseNum)
                || Objects.equals(log.getTargetWarehouse(), warehouseNum)
                || (log.getSourceWarehouse() == null && log.getTargetWarehouse() == null);
    }

    private static int sumAmount(List<InventoryLog> logs, Integer targetLogType) {
        return logs.stream()
                .filter(log -> Objects.equals(log.getLogType(), targetLogType))
                .mapToInt(log -> Math.abs(log.getAmountChange() == null ? 0 : log.getAmountChange()))
                .sum();
    }

    private static int normalizeDays(Integer days) {
        if (days == null || days < 1) {
            return DEFAULT_LOG_DAYS;
        }
        return Math.min(days, MAX_LOG_DAYS);
    }

    private static int normalizeLogLimit(Integer limit) {
        if (limit == null || limit < 1) {
            return DEFAULT_LOG_LIMIT;
        }
        return Math.min(limit, MAX_LOG_LIMIT);
    }

    private static void validateWarehouseNum(Integer warehouseNum) {
        if (warehouseNum == null || warehouseNum <= 0) {
            throw new IllegalArgumentException("warehouseNum 非法");
        }
    }

    private static boolean isAllowedApprovalRole(Role role, Long roleId) {
        if (roleId != null && (roleId == 1L || roleId == 2L)) {
            return true;
        }
        if (role == null || role.getRoleKey() == null) {
            return false;
        }
        String normalizedRoleKey = role.getRoleKey().trim().toLowerCase(Locale.ROOT);
        return normalizedRoleKey.equals("admin")
                || normalizedRoleKey.equals("warehouse_manager")
                || normalizedRoleKey.equals("warehouse-admin");
    }

    private static String resolveRoleKey(Role role, Long roleId) {
        if (role != null && role.getRoleKey() != null && !role.getRoleKey().isBlank()) {
            return role.getRoleKey();
        }
        return roleId == null ? null : "role-" + roleId;
    }

    private static String requireText(String value, String fieldName) {
        String normalized = McpSupport.normalizeBlank(value);
        if (normalized == null) {
            throw new IllegalArgumentException(fieldName + " 不能为空");
        }
        return normalized;
    }

    private static String generateApprovalId() {
        String timePart = String.valueOf(Instant.now().toEpochMilli());
        String suffix = UUID.randomUUID().toString().replace("-", "").substring(0, 6).toUpperCase(Locale.ROOT);
        return "AP" + timePart + suffix;
    }
}
