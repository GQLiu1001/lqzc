package com.lqzc.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lqzc.common.Result;
import com.lqzc.common.constant.LogConstant;
import com.lqzc.common.domain.InventoryItem;
import com.lqzc.common.domain.InventoryLog;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.common.req.LogsChangeReq;
import com.lqzc.common.req.LogsInboundReq;
import com.lqzc.common.req.LogsTransferReq;
import com.lqzc.common.resp.LogsListResp;
import com.lqzc.aspect.LianqingLogin;
import com.lqzc.service.InventoryItemService;
import com.lqzc.service.InventoryLogService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.Resource;
import org.springframework.beans.BeanUtils;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.Objects;

@Tag(name = "出入库日志管理相关接口")
@RestController
@RequestMapping("/logs")
public class LogsController {
    @Resource
    private InventoryLogService inventoryLogService;
    @Resource
    private InventoryItemService inventoryItemService;
    /**
     * 查询出入库及调拨记录
     */
    @Operation(summary = "查询出入库及调拨记录", description = "根据条件分页查询出入库和调拨记录")
    @GetMapping("/list")
    public Result<LogsListResp> list(@Parameter(description = "当前页码") @RequestParam(defaultValue = "1") Integer current,
                         @Parameter(description = "每页数量") @RequestParam(defaultValue = "10") Integer size,
                         @Parameter(description = "日志类型", required = true) @RequestParam Integer logType,
                         @Parameter(description = "开始时间") @RequestParam(required = false) String startTime,
                         @Parameter(description = "结束时间") @RequestParam(required = false) String endTime) {
        IPage<InventoryLog> page = new Page<>(current, size);
        if (startTime != null) {
            startTime = startTime.substring(0, 10);
        }
        if (endTime != null) {
            endTime = endTime.substring(0, 10);
        }
        IPage<InventoryLog> record = inventoryLogService.getLog(page, startTime, endTime, logType);
        LogsListResp resp = new LogsListResp();
        resp.setRecords(record.getRecords());
        resp.setTotal(record.getTotal());
        resp.setSize(record.getSize());
        resp.setCurrent(record.getCurrent());
        return Result.success(resp);
    }
    
    /**
     * 修改出入库或调拨记录
     */
    @Transactional(rollbackFor = Exception.class)
    @Operation(summary = "修改出入库或调拨记录", description = "修改现有的出入库或调拨记录信息")
    @PutMapping("/change")
    public Result<?> change(@Parameter(description = "日志修改请求参数", required = true) @RequestBody LogsChangeReq request) {
        // 前端:id:1:change:40 -> 修改change为30 ->前端:id:3:change:30 (多出一条冲正记录)
        // 前端修改id为x的log，修改后的数据为request
        // 取出id
        System.out.println("request = " + request);
        Long logId = request.getId();
        //冲正
        //首先 通过前端正在操作的id找出记录
        InventoryLog inventoryLog = inventoryLogService.getById(logId);
        inventoryLog.setLogType(4);
        inventoryLogService.updateById(inventoryLog);
        //冲正log
        inventoryLogService.logReversal(inventoryLog);
        //冲正item
        inventoryLog.setLogType(request.getLogType());
        inventoryItemService.itemReversal(inventoryLog);

        //处理req 传递过来的请求
        //调库
        if (Objects.equals(request.getLogType(), LogConstant.TRANSFER)) {
            LogsTransferReq transReq = new LogsTransferReq();
            BeanUtils.copyProperties(request, transReq);
            this.transfer(transReq);
        }
        //入库
        if (Objects.equals(request.getLogType(), LogConstant.INBOUND)) {
            LogsInboundReq postReq = new LogsInboundReq();
            InventoryItem byId = inventoryItemService.getById(request.getItemId());
            BeanUtils.copyProperties(byId, postReq);
            postReq.setTotalAmount(request.getAmountChange());
            this.inbound(postReq);
        }
        return Result.success();
    }

    /**
     * 创建入库记录
     */
    @Transactional(rollbackFor = Exception.class)
    @Operation(summary = "创建入库记录", description = "创建新的入库记录")
    @PostMapping("/inbound")
    public Result<?> inbound(@Parameter(description = "入库请求参数", required = true) @RequestBody LogsInboundReq request) {
        //产品分类胶和洁具特殊设置unitPerBox
        if (request.getCategory() >= 3) {
            request.setUnitPerBox(1);
        }
        //方法主要有两个作用 1.入库更新items 如果没有就新insert一个
        //                2.创建一个入库logs
        //更新库存
        System.out.println("触发更新库存 request = " + request);
        Long itemId = inventoryItemService.postInboundItem(request);
        //更新log
        inventoryLogService.postInboundLog(request,itemId);
        return Result.success();
    }
    
    /**
     * 创建调拨记录
     */
    @Transactional(rollbackFor = Exception.class)
    @Operation(summary = "创建调拨记录", description = "创建新的调拨记录")
    @PostMapping("/transfer")
    public Result<?> transfer(@Parameter(description = "调拨请求参数", required = true) @RequestBody LogsTransferReq request) {
        //校验仓库数
        if ((request.getSourceWarehouse() >= 5 || request.getSourceWarehouse() <= 0)
                ||
                (request.getTargetWarehouse() >= 5 || request.getTargetWarehouse() <= 0)) {
            throw new LianqingException("不存在目标仓库");
        }
        //方法主要有两个作用 1.调库更新items的信息 (改个warehouse_num)
        //                2.创建一个log
        //更新
        inventoryItemService.postTransferItem(request.getItemId(),request.getSourceWarehouse(),request.getTargetWarehouse());
        inventoryLogService.postTransferLog(request);
        return Result.success();
    }
    
    /**
     * 删除日志记录
     */
    @LianqingLogin
    @Operation(summary = "删除日志记录", description = "根据记录ID删除日志记录")
    @DeleteMapping("/delete/{id}")
    public Result<?> delete(@Parameter(description = "日志记录ID", required = true) @PathVariable Long id) {
        inventoryLogService.removeById(id);
        return Result.success();
    }
}
