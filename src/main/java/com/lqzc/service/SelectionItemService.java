package com.lqzc.service;

import com.lqzc.common.domain.SelectionItem;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.records.SelectionItemsRecord;
import com.lqzc.common.req.MallOrderReq;
import com.lqzc.common.req.SelectionItemAddReq;

import java.util.List;

/**
* @author 11965
* @description 针对表【selection_item(选品单明细表)】的数据库操作Service
* @createDate 2025-07-11 09:05:49
*/
public interface SelectionItemService extends IService<SelectionItem> {
    List<SelectionItemsRecord> getSelectionListDetail(Long id);

    void addNewItem2List(SelectionItemAddReq req, Long id);

    void updateSelectionListDetailAmount(Integer amount, Long listId, Long itemId);

    List<SelectionItem> getList(Long selectionListId);

    void deleteSelectionListDetail(Long itemId, Long listId);

    void deleteSelectionList(Long id);

    void addSellectionListItems(MallOrderReq mallOrderReq, Long id);
}
