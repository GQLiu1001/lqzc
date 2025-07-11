package com.lqzc.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lqzc.common.Result;
import com.lqzc.common.constant.DispatchConstant;
import com.lqzc.common.constant.DriverStatusConstant;
import com.lqzc.common.records.DispatchOrderFetchRecords;
import com.lqzc.common.records.DispatchOrderListRecord;
import com.lqzc.common.resp.DispatchOrderFetchResp;
import com.lqzc.common.resp.DispatchOrderListResp;
import com.lqzc.utils.UserContextHolder;
import com.lqzc.service.DriverService;
import com.lqzc.service.OrderInfoService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.Resource;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

@Tag(name = "派送系统订单管理相关接口")
@RestController
@RequestMapping("/delivery")
public class DeliveryController {
    @Resource
    private OrderInfoService orderInfoService;
    @Resource
    private DriverService driverService;
    /**
     * 获取派送订单列表
     */
    @Operation(summary = "获取派送订单列表", description = "分页获取派送订单列表")
    @GetMapping("/list")
    public Result<DispatchOrderListResp> list(@Parameter(description = "当前页码") @RequestParam(defaultValue = "1") Integer current ,
                                              @Parameter(description = "每页数量") @RequestParam(defaultValue = "10") Integer size) {
        IPage<DispatchOrderListRecord> pageNum = new Page<>(current, size);
        IPage<DispatchOrderListRecord> records = orderInfoService.getList(pageNum);
        DispatchOrderListResp resp = new DispatchOrderListResp();
        resp.setRecords(records.getRecords());
        resp.setTotal(records.getTotal());
        return Result.success(resp);
    }

    /**
     * 获取可用派送新订单
     */
    @Operation(summary = "获取可用派送新订单", description = "获取可被司机抢单的新订单列表")
    @GetMapping("/fetch/{status}")
    public Result<DispatchOrderFetchResp> fetch(@Parameter(description = "当前页码") @RequestParam(defaultValue = "1") Integer current,
                                                @Parameter(description = "每页数量") @RequestParam(defaultValue = "10") Integer size,
                                                @PathVariable Integer status) {
        IPage<DispatchOrderFetchRecords> page = new Page<>(current, size);
        IPage<DispatchOrderFetchRecords> record = orderInfoService.fetch(page,status);
        DispatchOrderFetchResp resp = new DispatchOrderFetchResp();
        resp.setRecords(record.getRecords());
        resp.setTotal(record.getTotal());
        resp.setCurrent(record.getCurrent());
        resp.setSize(record.getSize());
        return Result.success(resp);
    }

    /**
     * 司机抢单
     */
    @Operation(summary = "司机抢单", description = "司机抢取指定订单")
    @PostMapping("/rob/{id}/{orderNo}")
    public Result<Boolean> rob(@Parameter(description = "司机ID", required = true) @PathVariable Long id,
                              @Parameter(description = "订单号", required = true) @PathVariable String orderNo) {
        Boolean resp = orderInfoService.robNewOrder(id,orderNo);
        return resp?Result.success():Result.fail();
    }

    /**
     * 完成派送订单
     */
    @Transactional(rollbackFor = Exception.class)
    @Operation(summary = "完成派送订单", description = "标记订单为已完成派送")
    @PostMapping("/complete/{orderNo}")
    public Result<?> complete(@Parameter(description = "订单号", required = true) @PathVariable String orderNo) {
        orderInfoService.changeOrderDispatchStatus(orderNo,DispatchConstant.FINISH_DISPATCH);
        driverService.changeStatus(UserContextHolder.getDriverId(), DriverStatusConstant.FREE);
        return Result.success();
    }

    /**
     * 取消派送订单
     */
    @Operation(summary = "取消派送订单", description = "取消指定订单的派送")
    @PostMapping("/cancel/{orderNo}")
    public Result<?> cancel(@Parameter(description = "订单号", required = true) @PathVariable String orderNo) {
        orderInfoService.changeOrderDispatchStatus(orderNo, DispatchConstant.WAITING_DISPATCH);
        return Result.success();
    }
}
