package com.lqzc.controller;

import com.lqzc.common.Result;
import com.lqzc.common.req.PayCreateReq;
import com.lqzc.common.resp.PayCreateResp;
import com.lqzc.common.resp.PayStatusResp;
import com.lqzc.service.OrderPaymentService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@Tag(name = "C端-支付")
@RestController
@RequestMapping("/mall/pay")
@RequiredArgsConstructor
public class MallPayController {

    private final OrderPaymentService orderPaymentService;

    @Operation(summary = "发起支付")
    @PostMapping("/create")
    public Result<PayCreateResp> create(@RequestBody PayCreateReq req) {
        // TODO 支付模拟
        return Result.success(new PayCreateResp());
    }

    @Operation(summary = "查询支付状态")
    @GetMapping("/status/{orderNo}")
    public Result<PayStatusResp> status(@PathVariable String orderNo) {
        // TODO 查询支付状态
        return Result.success(new PayStatusResp());
    }
}
