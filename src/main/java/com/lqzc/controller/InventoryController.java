package com.lqzc.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lqzc.common.Result;
import com.lqzc.common.domain.InventoryItem;
import com.lqzc.common.req.ItemsChangeReq;
import com.lqzc.common.resp.IetmsFetchResp;
import com.lqzc.common.resp.ItemsListResp;
import com.lqzc.service.InventoryItemService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.Resource;
import org.springframework.web.bind.annotation.*;

@Tag(name = "库存管理相关接口")
@RestController
@RequestMapping("/inventory")
public class InventoryController {
    @Resource
    private InventoryItemService inventoryItemService;
    /**
     * 查询库存列表
     */
    @Operation(summary = "查询库存列表", description = "根据条件分页查询库存商品列表")
    @GetMapping("/items-list")
    public Result<ItemsListResp> itemsList(@Parameter(description = "当前页码") @RequestParam(defaultValue = "1") Integer current, 
                              @Parameter(description = "每页数量") @RequestParam(defaultValue = "10") Integer size,
                              @Parameter(description = "商品类别") @RequestParam(required = false) String category,
                              @Parameter(description = "商品表面") @RequestParam(required = false) String surface) {
        IPage<InventoryItem> page = new Page<>(current, size);
        IPage<InventoryItem> record = inventoryItemService.getList(page,category,surface);
        ItemsListResp resp = new ItemsListResp();
        resp.setRecords(record.getRecords());
        resp.setTotal(record.getTotal());
        resp.setCurrent(record.getCurrent());
        resp.setSize(record.getSize());
        return Result.success(resp);
    }
    
    /**
     * 修改库存商品
     */
    @Operation(summary = "修改库存商品", description = "修改库存商品信息")
    @PutMapping("/items-change")
    public Result<?> itemsChange(@Parameter(description = "库存修改请求参数", required = true) @RequestBody ItemsChangeReq request) {
        inventoryItemService.itemsChange(request);
        return Result.success();
    }
    
    /**
     * 删除库存id商品
     */
    @Operation(summary = "删除库存商品", description = "根据商品ID删除库存商品")
    @DeleteMapping("/items-delete/{id}")
    public Result<?> itemsDelete(@Parameter(description = "商品ID", required = true) @PathVariable Long id) {
        inventoryItemService.removeById(id);
        return Result.success();
    }
    
    /**
     * 根据型号自动回填 ID 和数量
     */
    @Operation(summary = "根据型号获取商品信息", description = "根据商品型号自动回填ID和数量信息")
    @GetMapping("/fetch/{model}")
    public Result<IetmsFetchResp> fetch(@Parameter(description = "商品型号", required = true) @PathVariable String model) {
        InventoryItem model1 = inventoryItemService.query().eq("model", model).one();
        IetmsFetchResp resp = new IetmsFetchResp();
        resp.setId(model1.getId());
        resp.setTotalAmount(model1.getTotalAmount());
        return Result.success(resp);
    }
}
