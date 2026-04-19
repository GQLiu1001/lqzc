package com.lqzc.mcp.support;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public final class McpSupport {

    private static final ThreadLocal<SimpleDateFormat> DATE_TIME_FORMAT = ThreadLocal.withInitial(
            () -> new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.CHINA)
    );

    private McpSupport() {
    }

    public static String formatDateTime(Date value) {
        return value == null ? null : DATE_TIME_FORMAT.get().format(value);
    }

    public static String normalizeBlank(String value) {
        if (value == null) {
            return null;
        }
        String normalized = value.trim();
        return normalized.isEmpty() ? null : normalized;
    }

    public static String warehouseLabel(Integer warehouseNum) {
        return warehouseNum == null ? "未知仓库" : "仓库" + warehouseNum;
    }

    public static String categoryLabel(Integer category) {
        return switch (category) {
            case 1 -> "墙砖";
            case 2 -> "地砖";
            case 3 -> "胶";
            case 4 -> "洁具";
            default -> "未知";
        };
    }

    public static String surfaceLabel(Integer surface) {
        return switch (surface) {
            case 1 -> "抛光";
            case 2 -> "哑光";
            case 3 -> "釉面";
            case 4 -> "通体大理石";
            case 5 -> "微晶石";
            case 6 -> "岩板";
            default -> "未知";
        };
    }

    public static String inventoryLogTypeLabel(Integer logType) {
        return switch (logType) {
            case 1 -> "入库";
            case 2 -> "出库";
            case 3 -> "调拨";
            case 4 -> "冲正";
            default -> "未知";
        };
    }

    public static String orderStatusLabel(Integer orderStatus, Integer dispatchStatus, String cancelReason) {
        if (orderStatus == null) {
            return "未知";
        }
        return switch (orderStatus) {
            case 0 -> "待支付";
            case 1 -> "待发货";
            case 2 -> "配送中";
            case 3 -> "待确认";
            case 4 -> isCancelled(dispatchStatus, cancelReason) ? "已取消" : "已完成";
            case 5 -> "已关闭";
            default -> "未知";
        };
    }

    public static String payStatusLabel(Integer payStatus) {
        return switch (payStatus) {
            case 0 -> "未支付";
            case 1 -> "已支付";
            case 2 -> "部分退款";
            case 3 -> "已退款";
            default -> "未知";
        };
    }

    public static String dispatchStatusLabel(Integer dispatchStatus) {
        return switch (dispatchStatus) {
            case 0 -> "待派送";
            case 1 -> "待接单";
            case 2 -> "派送中";
            case 3 -> "已完成";
            default -> "未知";
        };
    }

    public static String driverWorkStatusLabel(Integer workStatus) {
        return switch (workStatus) {
            case 0 -> "空闲";
            case 1 -> "忙碌";
            case 2 -> "离线";
            default -> "未知";
        };
    }

    public static String maskPhone(String phone) {
        String normalized = normalizeBlank(phone);
        if (normalized == null || normalized.length() < 7) {
            return normalized;
        }
        return normalized.substring(0, 3) + "****" + normalized.substring(normalized.length() - 4);
    }

    private static boolean isCancelled(Integer dispatchStatus, String cancelReason) {
        if (cancelReason != null && !cancelReason.isBlank()) {
            return true;
        }
        return dispatchStatus == null || dispatchStatus != 3;
    }
}
