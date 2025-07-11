package com.lqzc.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lqzc.common.Result;
import com.lqzc.common.records.MallItemsListRecord;
import com.lqzc.common.resp.MallItemsListResp;
import com.lqzc.service.InventoryItemService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.Resource;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "商城系统展示物品相关接口")
@RestController
@RequestMapping("/mall/items")
public class ItemsController {
    @Resource
    private InventoryItemService inventoryItemService;

    @Operation(summary = "获取展示信息")
    @GetMapping("/list")
    public Result<MallItemsListResp> getItemsList(@Parameter(description = "当前页码") @RequestParam(defaultValue = "1") Integer current ,
                                                  @Parameter(description = "每页数量") @RequestParam(defaultValue = "10") Integer size,
                                                  @Parameter(description = "商品类别") @RequestParam(required = false) String category,
                                                  @Parameter(description = "商品表面") @RequestParam(required = false) String surface) {
        IPage<MallItemsListRecord> page = new Page<>(current, size);
        IPage<MallItemsListRecord> record = inventoryItemService.getItemsList(page,category,surface);
        MallItemsListResp resp = new MallItemsListResp();
        resp.setRecords(record.getRecords());
        resp.setTotal(record.getTotal());
        resp.setCurrent(record.getCurrent());
        resp.setSize(record.getSize());
        return Result.success(resp);
    }
}
