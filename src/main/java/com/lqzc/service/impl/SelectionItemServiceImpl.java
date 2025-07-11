package com.lqzc.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.domain.InventoryItem;
import com.lqzc.common.domain.SelectionItem;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.common.records.SelectionItemsRecord;
import com.lqzc.common.req.MallOrderReq;
import com.lqzc.common.req.SelectionItemAddReq;
import com.lqzc.mapper.InventoryItemMapper;
import com.lqzc.service.SelectionItemService;
import com.lqzc.mapper.SelectionItemMapper;
import jakarta.annotation.Resource;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

/**
 * @author 11965
 * @description 针对表【selection_item(选品单明细表)】的数据库操作Service实现
 * @createDate 2025-07-11 09:05:49
 */
@Service
public class SelectionItemServiceImpl extends ServiceImpl<SelectionItemMapper, SelectionItem>
        implements SelectionItemService {

    @Resource
    private SelectionItemMapper selectionItemMapper;
    @Resource
    private InventoryItemMapper inventoryItemMapper;

    @Override
    public List<SelectionItemsRecord> getSelectionListDetail(Long id) {
        LambdaQueryWrapper<SelectionItem> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(SelectionItem::getSelectionId, id);
        List<SelectionItem> selectionItems = selectionItemMapper.selectList(queryWrapper);
        List<SelectionItemsRecord> selectionItemsRecords = new ArrayList<>();
        for (SelectionItem selectionItem : selectionItems) {
            SelectionItemsRecord selectionItemsRecord = new SelectionItemsRecord();
            BeanUtils.copyProperties(selectionItem, selectionItemsRecord);
            selectionItemsRecords.add(selectionItemsRecord);
        }
        return selectionItemsRecords;
    }

    @Transactional(rollbackFor = Exception.class)
    @Override
    public void addSellectionListItems(MallOrderReq mallOrderReq, Long selId) {
        mallOrderReq.getItems().forEach(item -> {
            SelectionItem selectionItem = new SelectionItem();
            BeanUtils.copyProperties(item, selectionItem);
            selectionItem.setSelectionId(selId);
            LambdaQueryWrapper<InventoryItem> queryWrapper = new LambdaQueryWrapper<InventoryItem>();
            queryWrapper.eq(InventoryItem::getModel, item.getModel());
            InventoryItem inventoryItem = inventoryItemMapper.selectOne(queryWrapper);
            selectionItem.setItemSpecification(inventoryItem.getSpecification());
            selectionItem.setItemSellingPrice(inventoryItem.getSellingPrice());
            selectionItem.setItemModel(inventoryItem.getModel());
            int insert = selectionItemMapper.insert(selectionItem);
            if (insert != 1) {
                throw new LianqingException("插入selectionItemMapper:" + selectionItem + "失败");
            }
        });
    }

    @Transactional(rollbackFor = Exception.class)
    @Override
    public void addNewItem2List(SelectionItemAddReq req, Long id) {
        System.out.println("req = " + req);
        LambdaQueryWrapper<InventoryItem> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(InventoryItem::getModel, req.getItemModel());
        InventoryItem inventoryItem = inventoryItemMapper.selectOne(queryWrapper);
        SelectionItem selectionItem = new SelectionItem();
        selectionItem.setSelectionId(id);
        selectionItem.setItemSpecification(inventoryItem.getSpecification());
        BeanUtils.copyProperties(req, selectionItem);
        selectionItemMapper.insert(selectionItem);
    }

    @Transactional(rollbackFor = Exception.class)
    @Override
    public void updateSelectionListDetailAmount(Integer amount, Long listId, Long itemId) {
        LambdaQueryWrapper<SelectionItem> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(SelectionItem::getSelectionId, listId);
        queryWrapper.eq(SelectionItem::getId, itemId);
        SelectionItem selectionItem = selectionItemMapper.selectOne(queryWrapper);
        selectionItem.setAmount(amount);
        selectionItemMapper.updateById(selectionItem);
    }

    @Override
    public List<SelectionItem> getList(Long selectionListId) {
        LambdaQueryWrapper<SelectionItem> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(SelectionItem::getSelectionId, selectionListId);
        return selectionItemMapper.selectList(queryWrapper);
    }

    @Override
    public void deleteSelectionListDetail(Long itemId, Long listId) {
        LambdaQueryWrapper<SelectionItem> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(SelectionItem::getSelectionId, listId);
        queryWrapper.eq(SelectionItem::getId, itemId);
        selectionItemMapper.delete(queryWrapper);
    }

    @Override
    public void deleteSelectionList(Long id) {
        LambdaQueryWrapper<SelectionItem> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(SelectionItem::getSelectionId, id);
        selectionItemMapper.delete(queryWrapper);
    }

}




