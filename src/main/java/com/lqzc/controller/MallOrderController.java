package com.lqzc.controller;

import com.lqzc.common.Result;
import com.lqzc.common.req.OrderCreateReq;
import com.lqzc.common.req.OrderPreviewReq;
import com.lqzc.common.resp.ConfirmReceiveResp;
import com.lqzc.common.resp.MallOrderDetailResp;
import com.lqzc.common.resp.OrderCreateResp;
import com.lqzc.common.resp.OrderListItemResp;
import com.lqzc.common.resp.OrderPreviewResp;
import com.lqzc.common.PageResp;
import com.lqzc.service.OrderInfoService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.Collections;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@Tag(name = "C端-订单")
@RestController
@RequestMapping("/mall/order")
@RequiredArgsConstructor
public class MallOrderController {

    private final OrderInfoService orderInfoService;

    @Operation(summary = "订单结算预览")
    @PostMapping("/preview")
    public Result<OrderPreviewResp> preview(@RequestBody OrderPreviewReq req) {
        // TODO 计算金额与最优券
        return Result.success(new OrderPreviewResp());
    }

    @Operation(summary = "创建订单")
    @PostMapping("/create")
    public Result<OrderCreateResp> create(@RequestBody OrderCreateReq req) {
        // TODO 创建订单
        return Result.success(new OrderCreateResp());
    }

    @Operation(summary = "订单列表")
    @GetMapping("/list")
    public Result<PageResp<OrderListItemResp>> list(@RequestParam(required = false) Integer status,
                                                    @RequestParam(defaultValue = "1") Integer current,
                                                    @RequestParam(defaultValue = "10") Integer size) {
        PageResp<OrderListItemResp> page = new PageResp<>();
        page.setTotal(0L);
        page.setRecords(Collections.emptyList());
        return Result.success(page);
    }

    @Operation(summary = "订单详情")
    @GetMapping("/detail/{orderNo}")
    public Result<MallOrderDetailResp> detail(@PathVariable String orderNo) {
        // TODO 查询详情
        return Result.success(new MallOrderDetailResp());
    }

    @Operation(summary = "取消订单")
    @PostMapping("/cancel/{orderNo}")
    public Result<Void> cancel(@PathVariable String orderNo, @RequestParam(required = false) String reason) {
        // TODO 取消订单
        return Result.success();
    }

    @Operation(summary = "确认收货")
    @PostMapping("/confirm/{orderNo}")
    public Result<ConfirmReceiveResp> confirm(@PathVariable String orderNo) {
        // TODO 确认收货并发放积分
        return Result.success(new ConfirmReceiveResp());
    }
}
