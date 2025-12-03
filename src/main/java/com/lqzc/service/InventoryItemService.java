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
 * @author rabbittank
 * @description 针对表【inventory_item(瓷砖库存表)】的数据库操作Service
 * @createDate 2025-07-11 09:05:49
 */
public interface InventoryItemService extends IService<InventoryItem> {

    /**
     * 分页查询库存列表
     * <p>
     * 支持按品类和表面类型筛选。
     * </p>
     *
     * @param page     分页对象
     * @param category 品类筛选
     * @param surface  表面类型筛选
     * @return 库存分页数据
     */
    IPage<InventoryItem> getList(IPage<InventoryItem> page, String category, String surface);

    /**
     * 修改库存项信息
     *
     * @param request 库存变更请求参数
     */
    void itemsChange(ItemsChangeReq request);

    /**
     * 出库操作
     * <p>
     * 批量减少库存数量。
     * </p>
     *
     * @param items 出库商品列表
     */
    void postOutboundItem(List<OrderNewReq.OrderNewItem> items);

    /**
     * 入库操作
     * <p>
     * 新增或增加库存数量。
     * </p>
     *
     * @param request 入库请求参数
     * @return 入库的库存项ID
     */
    Long postInboundItem(LogsInboundReq request);

    /**
     * 调拨操作
     * <p>
     * 将库存从一个仓库转移到另一个仓库。
     * </p>
     *
     * @param itemId          库存项ID
     * @param sourceWarehouse 源仓库
     * @param targetWarehouse 目标仓库
     */
    void postTransferItem(Long itemId, Integer sourceWarehouse, Integer targetWarehouse);

    /**
     * 分页查询商城商品列表
     * <p>
     * C端商城使用的商品列表查询。
     * </p>
     *
     * @param page     分页对象
     * @param category 品类筛选
     * @param surface  表面类型筛选
     * @return 商品分页数据
     */
    IPage<MallItemsListRecord> getItemsList(IPage<MallItemsListRecord> page, String category, String surface);

    /**
     * 库存冲正
     * <p>
     * 根据库存日志进行库存冲正操作。
     * </p>
     *
     * @param inventoryLog 库存日志对象
     */
    void itemReversal(InventoryLog inventoryLog);
}
