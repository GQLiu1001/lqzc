package com.lqzc.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.InventoryItem;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.domain.InventoryLog;
import com.lqzc.common.records.MallItemsListRecord;
import com.lqzc.common.req.ItemsChangeReq;
import com.lqzc.common.req.LogsInboundReq;
import com.lqzc.common.req.OrderNewReq;

import java.util.List;

/**
 * @author 11965
 * @description 针对表【inventory_item(瓷砖库存表)】的数据库操作Service
 * @createDate 2025-07-11 09:05:49
 */
public interface InventoryItemService extends IService<InventoryItem> {

    IPage<InventoryItem> getList(IPage<InventoryItem> page, String category, String surface);


    void itemsChange(ItemsChangeReq request);

    void postOutboundItem(List<OrderNewReq.OrderNewItem> items);

    Long postInboundItem(LogsInboundReq request);

    void postTransferItem(Long itemId, Integer sourceWarehouse, Integer targetWarehouse);

    IPage<MallItemsListRecord> getItemsList(IPage<MallItemsListRecord> page, String category, String surface);

    void itemReversal(InventoryLog inventoryLog);
}
