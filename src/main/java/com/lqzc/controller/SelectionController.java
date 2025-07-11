package com.lqzc.controller;


import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lqzc.common.Result;
import com.lqzc.common.domain.InventoryItem;
import com.lqzc.common.domain.SelectionItem;
import com.lqzc.common.domain.SelectionList;
import com.lqzc.common.records.SelectionItemsRecord;
import com.lqzc.common.req.OrderNewReq;
import com.lqzc.common.req.SelectionItemAddReq;
import com.lqzc.common.req.SelectionListChangeReq;
import com.lqzc.common.resp.SelectionListPagedResp;
import com.lqzc.service.*;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.Resource;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

@Tag(name = "预约单管理相关接口")
@RestController
@RequestMapping("/selection")
public class SelectionController {

    @Resource
    private SelectionListService selectionListService;

    @Resource
    private SelectionItemService selectionItemService;
    @Resource
    private InventoryLogService inventoryLogService;
    @Resource
    private InventoryItemService inventoryItemService;
    @Resource
    private OrderInfoService orderInfoService;

    @GetMapping("/lists")
    @Operation(summary = "分页查询选品单列表", description = "供后台销售人员查看所有来自线上的客户意向单。")
    public Result<SelectionListPagedResp> getSelectionList(@Parameter(description = "当前页码") @RequestParam(defaultValue = "1") Integer current,
                                                   @Parameter(description = "每页数量") @RequestParam(defaultValue = "10") Integer size,
                                                   @Parameter(description = "选品单No") @RequestParam(required = false) String selectionNo,
                                                   @Parameter(description = "预约客户电话") @RequestParam(required = false) String customerPhone,
                                                   @Parameter(description = "按处理状态筛选 (0=待跟进, 1=已联系, 2=已到店, 3=已失效)") @RequestParam(required = false) Integer status){
        IPage<SelectionList> page = new Page<>(current, size);
        IPage<SelectionList> record = selectionListService.getSelectionList(page,selectionNo,customerPhone,status);
        SelectionListPagedResp resp = new SelectionListPagedResp();
        resp.setRecords(record.getRecords());
        resp.setTotal(record.getTotal());
        resp.setCurrent(record.getCurrent());
        resp.setSize(record.getSize());
        return Result.success(resp);
    }

    @GetMapping("/lists/{id}")
    @Operation(summary = "查询选品单详情", description = "查看指定选品单的详细内容，包括所有商品明细。")
     public Result<List<SelectionItemsRecord>> getSelectionListDetail(@PathVariable Long id){
        return Result.success(selectionItemService.getSelectionListDetail(id));
    }


    @PutMapping("/lists/{id}/status/{status}")
    @Operation(summary = "更新选品单处理状态", description = "销售人员跟进后，手动更新选品单的状态。")
    public Result<?> updateSelectionStatus(@PathVariable Long id, @PathVariable Integer status){
        selectionListService.updateSelectionStatus(id,status);
        return Result.success();
    }


    @PutMapping("/lists/{id}")
    @Operation(summary = "修改选品单主信息", description = "用于修改客户电话、派送地址、备注或状态等，不涉及商品明细的修改")
    public Result<?> updateSelectionList(@RequestBody SelectionListChangeReq req, @PathVariable Long id){
        selectionListService.updateSelectionList(req,id);
        return Result.success();
    }


    @PostMapping("/lists/{id}/items")
    @Operation(summary = "向选品单中添加新商品", description = "当客户决定增加一个原来清单里没有的商品时调用。")
    public Result<?> addNewItem2List(@RequestBody SelectionItemAddReq req, @PathVariable Long id){
        selectionItemService.addNewItem2List(req,id);
        return Result.success();
    }


    @PutMapping("/lists/{listId}/items/{itemId}")
    @Operation(summary = "修改选品单中某一项商品的数量", description = "用于更新某个已存在商品的数量")
    public Result<?> updateSelectionListDetailAmount(@RequestParam("amount") Integer amount, @PathVariable Long itemId, @PathVariable Long listId){
        selectionItemService.updateSelectionListDetailAmount(amount,listId,itemId);
        return Result.success();
    }


    @DeleteMapping("/lists/{listId}/items/{itemId}")
    @Operation(summary = "从选品单中删除某一项商品", description = "当客户决定不要某个商品时调用")
    public Result<?> deleteSelectionListDetail(@PathVariable Long itemId, @PathVariable Long listId){
        selectionItemService.deleteSelectionListDetail(itemId,listId);
        return Result.success();
    }

    @DeleteMapping("/lists/{id}")
    @Operation(summary = "删除选品单", description = "删除无效或已处理完成的选品单")
    @Transactional(rollbackFor = Exception.class)
    public Result<?> deleteSelectionList(@PathVariable Long id){
        selectionListService.deleteSelectionList(id);
        selectionItemService.deleteSelectionList(id);
        return Result.success();
    }

    /**
     * selectionListId
     */
    @PostMapping("/lists/order/{selectionListId}")
    @Operation(summary = "派发正式订单")
    @Transactional(rollbackFor = Exception.class)
    public Result<?> postOfficialOrder(@PathVariable Long selectionListId){
        final BigDecimal[] totalPrice = {new BigDecimal(0)};
        SelectionList byId = selectionListService.getById(selectionListId);
        List<SelectionItem> lists = selectionItemService.getList(selectionListId);
        OrderNewReq req = new OrderNewReq();
        List<OrderNewReq.OrderNewItem> items = new ArrayList<>();
        lists.forEach(item->{
            LambdaQueryWrapper<InventoryItem> queryWrapper = new LambdaQueryWrapper<>();
            queryWrapper.eq(InventoryItem::getModel,item.getItemModel());
            InventoryItem one = inventoryItemService.getOne(queryWrapper);

            OrderNewReq.OrderNewItem newItem = new OrderNewReq.OrderNewItem();
            newItem.setItemId(one.getId());
            newItem.setModel(item.getItemModel());
            newItem.setAmount(item.getAmount());
            BigDecimal itemSellingPrice = item.getItemSellingPrice();
            Integer amount = item.getAmount();
            newItem.setSubtotalPrice(itemSellingPrice.multiply(new BigDecimal(amount)));
            totalPrice[0] = totalPrice[0].add(newItem.getSubtotalPrice());
            items.add(newItem);
        });
        req.setItems(items);
        req.setRemark(byId.getRemark());
        req.setTotalPrice(totalPrice[0]);
        req.setCustomerPhone(byId.getCustomerPhone());
        //生成出库日志
        inventoryLogService.postOutboundLog(items);
        //扣除库存
        inventoryItemService.postOutboundItem(items);
        //创建订单 总订单派送状态0 添加子订单详细
        orderInfoService.newOrder(req,byId.getDeliveryAddress());
        byId.setStatus(3);
        selectionListService.updateById(byId);
        return Result.success();
    }
}
