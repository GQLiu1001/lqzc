package com.lqzc.controller;

import com.lqzc.common.Result;
import com.lqzc.common.resp.CouponMarketItemResp;
import com.lqzc.common.resp.MyCouponResp;
import com.lqzc.service.CouponTemplateService;
import com.lqzc.service.CustomerCouponService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.Collections;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@Tag(name = "C端-优惠券")
@RestController
@RequestMapping("/mall/coupon")
@RequiredArgsConstructor
public class MallCouponController {

    private final CouponTemplateService couponTemplateService;
    private final CustomerCouponService customerCouponService;

    @Operation(summary = "领券中心列表")
    @GetMapping("/market")
    public Result<List<CouponMarketItemResp>> market() {
        // TODO 查询可领取的券模板
        return Result.success(Collections.emptyList());
    }

    @Operation(summary = "领取优惠券")
    @PostMapping("/receive/{templateId}")
    public Result<Void> receive(@PathVariable Long templateId) {
        // TODO 领取优惠券
        return Result.success();
    }

    @Operation(summary = "我的优惠券")
    @GetMapping("/my-coupons")
    public Result<List<MyCouponResp>> myCoupons(@RequestParam(required = false) Integer status) {
        // TODO 查询当前用户的券
        return Result.success(Collections.emptyList());
    }
}
