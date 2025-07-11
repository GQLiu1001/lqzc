package com.lqzc.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.InventoryLog;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.req.LogsInboundReq;
import com.lqzc.common.req.LogsTransferReq;
import com.lqzc.common.req.OrderNewReq;

import java.util.List;

/**
* @author 11965
* @description 针对表【inventory_log(库存操作日志表)】的数据库操作Service
* @createDate 2025-07-11 09:05:49
*/
public interface InventoryLogService extends IService<InventoryLog> {
    IPage<InventoryLog> getLog(IPage<InventoryLog> page, String startTime, String endTime, Integer logType);

    void postInboundLog(LogsInboundReq request, Long itemId);

    void postTransferLog(LogsTransferReq request);

    void postOutboundLog(List<OrderNewReq.OrderNewItem> items);

    void logReversal(InventoryLog inventoryLog);
}
