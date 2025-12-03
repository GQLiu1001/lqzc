package com.lqzc.service;

import com.lqzc.common.domain.SelectionItem;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.records.SelectionItemsRecord;
import com.lqzc.common.req.MallOrderReq;
import com.lqzc.common.req.SelectionItemAddReq;

import java.util.List;

/**
* @author rabbittank
* @description 针对表【selection_item(选品单明细表)】的数据库操作Service
* @createDate 2025-07-11 09:05:49
*/
public interface SelectionItemService extends IService<SelectionItem> {

    /**
     * 获取选品单明细列表
     *
     * @param id 选品单ID
     * @return 选品单明细记录列表
     */
    List<SelectionItemsRecord> getSelectionListDetail(Long id);

    /**
     * 向选品单添加新商品
     *
     * @param req 选品项添加请求
     * @param id  选品单ID
     */
    void addNewItem2List(SelectionItemAddReq req, Long id);

    /**
     * 更新选品单明细数量
     *
     * @param amount 新数量
     * @param listId 选品单ID
     * @param itemId 选品项ID
     */
    void updateSelectionListDetailAmount(Integer amount, Long listId, Long itemId);

    /**
     * 获取选品单的所有明细
     *
     * @param selectionListId 选品单ID
     * @return 选品项列表
     */
    List<SelectionItem> getList(Long selectionListId);

    /**
     * 删除选品单明细
     *
     * @param itemId 选品项ID
     * @param listId 选品单ID
     */
    void deleteSelectionListDetail(Long itemId, Long listId);

    /**
     * 删除选品单及其所有明细
     *
     * @param id 选品单ID
     */
    void deleteSelectionList(Long id);

    /**
     * 批量添加选品单明细
     * <p>
     * 商城下单场景批量添加商品。
     * </p>
     *
     * @param mallOrderReq 商城订单请求
     * @param id           选品单ID
     */
    void addSellectionListItems(MallOrderReq mallOrderReq, Long id);
}
