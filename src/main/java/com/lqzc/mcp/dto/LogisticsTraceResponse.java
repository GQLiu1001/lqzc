package com.lqzc.mcp.dto;

import java.util.List;

public record LogisticsTraceResponse(
        String orderNo,
        Integer orderStatus,
        String orderStatusLabel,
        Integer dispatchStatus,
        String dispatchStatusLabel,
        String logisticsStatus,
        String logisticsMessage,
        String expectedDeliveryTime,
        String receiveTime,
        DriverInfo driver,
        DriverLocation driverLocation,
        List<TraceEvent> timeline
) {
    public record DriverInfo(
            Long driverId,
            String driverName,
            String driverPhoneMasked,
            Integer workStatus,
            String workStatusLabel
    ) {
    }

    public record DriverLocation(
            Double latitude,
            Double longitude
    ) {
    }

    public record TraceEvent(
            String code,
            String title,
            String description,
            String time
    ) {
    }
}
