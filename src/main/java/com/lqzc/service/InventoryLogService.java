package com.lqzc.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.InventoryLog;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.req.LogsInboundReq;
import com.lqzc.common.req.LogsTransferReq;
import com.lqzc.common.req.OrderNewReq;

import java.util.List;

/**
* @author rabbittank
* @description 针对表【inventory_log(库存操作日志表)】的数据库操作Service
* @createDate 2025-07-11 09:05:49
*/
public interface InventoryLogService extends IService<InventoryLog> {

    /**
     * 分页查询库存操作日志
     * <p>
     * 支持按时间范围和日志类型筛选。
     * </p>
     *
     * @param page      分页对象
     * @param startTime 开始时间
     * @param endTime   结束时间
     * @param logType   日志类型
     * @return 日志分页数据
     */
    IPage<InventoryLog> getLog(IPage<InventoryLog> page, String startTime, String endTime, Integer logType);

    /**
     * 记录入库日志
     *
     * @param request 入库请求参数
     * @param itemId  库存项ID
     */
    void postInboundLog(LogsInboundReq request, Long itemId);

    /**
     * 记录调拨日志
     *
     * @param request 调拨请求参数
     */
    void postTransferLog(LogsTransferReq request);

    /**
     * 批量记录出库日志
     *
     * @param items 出库商品列表
     */
    void postOutboundLog(List<OrderNewReq.OrderNewItem> items);

    /**
     * 日志冲正
     * <p>
     * 撤销之前的库存操作。
     * </p>
     *
     * @param inventoryLog 库存日志对象
     */
    void logReversal(InventoryLog inventoryLog);
}
