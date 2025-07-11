package com.lqzc.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lqzc.common.Result;
import com.lqzc.common.domain.OrderDetail;
import com.lqzc.common.domain.OrderInfo;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.common.records.DispatchOrderFetchRecords;
import com.lqzc.common.records.OrderInfoRecords;
import com.lqzc.common.req.OrderChangeReq;
import com.lqzc.common.req.OrderDispatchReq;
import com.lqzc.common.req.OrderNewReq;
import com.lqzc.common.req.OrderSubChangeReq;
import com.lqzc.common.resp.DispatchOrderFetchResp;
import com.lqzc.common.resp.OrderDetailResp;
import com.lqzc.common.resp.OrderListResp;
import com.lqzc.service.InventoryItemService;
import com.lqzc.service.InventoryLogService;
import com.lqzc.service.OrderDetailService;
import com.lqzc.service.OrderInfoService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.Resource;
import org.springframework.beans.BeanUtils;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.Date;
import java.util.List;

@Tag(name = "订单管理相关接口")
@RestController
@RequestMapping("/orders")
public class OrdersController {
    @Resource
    private OrderInfoService orderInfoService;
    @Resource
    private OrderDetailService orderDetailService;
    @Resource
    private InventoryItemService inventoryItemService;
    @Resource
    private InventoryLogService inventoryLogService;
    /**
     * 创建新订单
     */
    @Transactional(rollbackFor = Exception.class)
    @Operation(summary = "创建新订单", description = "创建一个新的订单")
    @PostMapping("/new")
    public Result<?> newOrder(@Parameter(description = "新订单请求参数", required = true) @RequestBody OrderNewReq request) {
        //生成出库日志
        inventoryLogService.postOutboundLog(request.getItems());
        //扣除库存
        inventoryItemService.postOutboundItem(request.getItems());
        //创建订单 总订单派送状态0 添加子订单详细
        orderInfoService.newOrder(request);
        return Result.success();
    }
    
    /**
     * 查询订单列表
     */
    @Operation(summary = "查询订单列表", description = "根据条件分页查询订单列表")
    @GetMapping("/list")
    public Result<OrderListResp> list(@Parameter(description = "当前页码") @RequestParam(defaultValue = "1") Integer current,
                         @Parameter(description = "每页数量") @RequestParam(defaultValue = "10") Integer size,
                         @Parameter(description = "开始时间") @RequestParam(required = false) String startTime,
                         @Parameter(description = "结束时间") @RequestParam(required = false) String endTime,
                         @Parameter(description = "客户手机号") @RequestParam(required = false) String customerPhone) {
        IPage<OrderInfoRecords> page = new Page<>(current, size);
        String startStr = null;
        String endStr = null;
        if (startTime != null) {
            startStr = startTime.substring(0, 10);
        }
        if (endTime != null) {
            endStr = endTime.substring(0, 10);
        }
        IPage<OrderInfoRecords> resp = orderInfoService.getOrderList(page, size, startStr, endStr, customerPhone);
        OrderListResp orderListResp = new OrderListResp();
        orderListResp.setTotal(resp.getTotal());
        orderListResp.setRecords(resp.getRecords());
        orderListResp.setSize(resp.getSize());
        orderListResp.setCurrent(resp.getCurrent());
        return Result.success(orderListResp);
    }
    
    /**
     * 查询订单详情
     */
    @Operation(summary = "查询总订单的详情以及其子订单的详情", description = "根据订单ID查询订单详细信息")
    @GetMapping("/detail/{id}")
    public Result<OrderDetailResp> detail(@Parameter(description = "订单ID", required = true) @PathVariable Long id) {
        OrderDetailResp orderDetailResp = new OrderDetailResp();
        OrderInfo orderInfo = orderInfoService.getById(id);
        BeanUtils.copyProperties(orderInfo, orderDetailResp);
        List<OrderDetail> subOrderList = orderDetailService.list(new QueryWrapper<OrderDetail>().eq("order_id", orderInfo.getId()));
        orderDetailResp.setSubOrder(subOrderList);
        return Result.success(orderDetailResp);
    }
    
    /**
     * 修改总订单（不包括订单项变更）
     */
    @Operation(summary = "修改总订单", description = "修改订单主要信息，不包括订单项变更")
    @PutMapping("/change")
    public Result<?> change(@Parameter(description = "订单修改请求参数", required = true) @RequestBody OrderChangeReq request) {
        //只修改 电话 remark
        OrderInfo orderInfo = new OrderInfo();
        BeanUtils.copyProperties(request, orderInfo);
        orderInfo.setUpdateTime(new Date());
        boolean b = orderInfoService.updateById(orderInfo);
        if (!b) {
            throw new RuntimeException("总订单参数修改失败");
        }
        return Result.success();
    }

    /**
     * 修改指定子订单项信息
     */
    @Operation(summary = "修改子订单项", description = "修改指定子订单项的信息")
    @PutMapping("/change-sub")
    public Result<?> changeSub(@Parameter(description = "子订单修改请求参数", required = true) @RequestBody OrderSubChangeReq request) {
        //修改子订单 -> log item orderInfo orderDetail 以及 redis 热销榜都需更改
        //changeType -> 0：修改 1：添加 2：删除
        //req: orderDetail 的order_id item_id amount subtotal_price 以及InventoryItem 的model(item_id)
        Integer changeType = request.getChangeType();

        OrderDetail orderDetail = new OrderDetail();
        BeanUtils.copyProperties(request, orderDetail);

        orderDetailService.changeSubDetail(orderDetail,changeType);
        return Result.success();
    }

    
    /**
     * 删除主订单
     */
    @Transactional(rollbackFor = Exception.class)
    @Operation(summary = "删除主订单", description = "根据订单ID删除主订单")
    @DeleteMapping("/delete/{id}")
    public Result<?> delete(@Parameter(description = "订单ID", required = true) @PathVariable Long id) {
        //changeSub type2 删除子订单 -> log item orderInfo orderDetail 以及 redis 热销榜都需更改
        //先对子订单进行修改
        List<OrderDetail> orderDetails = orderDetailService.list(new QueryWrapper<OrderDetail>().eq("order_id", id));
        if (!orderDetails.isEmpty()) {
            orderDetails.forEach(orderDetail -> {
                orderDetailService.changeSubDetail(orderDetail,2);
            });
        }else {
            throw new LianqingException("删除主订单失败");
        }
        boolean b = orderInfoService.removeById(id);
        if (!b) {
            throw new LianqingException("删除主订单失败");
        }
        return Result.success();
    }

    
    /**
     * 更改订单派送状态
     */
    @Operation(summary = "更改订单派送状态", description = "修改订单的派送状态")
    @PutMapping("/change/dispatch-status/{id}/{status}")
    public Result<?> changeDispatchStatus(@Parameter(description = "订单ID", required = true) @PathVariable Long id, 
                                         @Parameter(description = "派送状态", required = true) @PathVariable Integer status) {
        orderInfoService.changeDispatchStatus(id,status);
        return Result.success();
    }

    /**
     * 派送订单
     */
    @Operation(summary = "派送新的订单", description = "派送新的订单")
    @PostMapping("/dispatch")
    public Result<?> dispatchOrder(@RequestBody OrderDispatchReq req) {
        orderInfoService.dispatchOrder(req);
        return Result.success();
    }

    /**
     * 获取可用派送新订单
     */
    @Operation(summary = "获取可用派送新订单", description = "获取可被司机抢单的新订单列表")
    @GetMapping("/fetch/{status}")
    public Result<DispatchOrderFetchResp> fetch(@Parameter(description = "当前页码") @RequestParam(defaultValue = "1") Integer current,
                                                @Parameter(description = "每页数量") @RequestParam(defaultValue = "10") Integer size,
                                                @Parameter(description = "开始时间") @RequestParam(required = false) String startTime,
                                                @Parameter(description = "结束时间") @RequestParam(required = false) String endTime,
                                                @Parameter(description = "客户手机号") @RequestParam(required = false) String customerPhone,
                                                @PathVariable Integer status) {
        String startStr = null;
        String endStr = null;
        if (startTime != null) {
            startStr = startTime.substring(0, 10);
        }
        if (endTime != null) {
            endStr = endTime.substring(0, 10);
        }
        IPage<DispatchOrderFetchRecords> page = new Page<>(current, size);
        IPage<DispatchOrderFetchRecords> record = orderInfoService.fetch(page,status,startStr,endStr,customerPhone);
        DispatchOrderFetchResp resp = new DispatchOrderFetchResp();
        resp.setRecords(record.getRecords());
        resp.setTotal(record.getTotal());
        resp.setCurrent(record.getCurrent());
        resp.setSize(record.getSize());
        return Result.success(resp);
    }
}
