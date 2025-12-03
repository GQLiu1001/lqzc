package com.lqzc.mapper;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.InventoryItem;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.lqzc.common.records.MallItemsListRecord;

/**
* @author rabbittank
* @description 针对表【inventory_item(瓷砖库存表)】的数据库操作Mapper
* @createDate 2025-07-11 09:05:49
* @Entity com.lqzc.common.domain.InventoryItem
*/
public interface InventoryItemMapper extends BaseMapper<InventoryItem> {
    IPage<MallItemsListRecord> getItemsList(IPage<MallItemsListRecord> page, String category, String surface);
    IPage<InventoryItem> getList(IPage<InventoryItem> page, String category, String surface);

    Integer itemReversal(Integer operationType, Long inventoryItemId, Integer sourceWarehouse, Integer quantityChange);
}




