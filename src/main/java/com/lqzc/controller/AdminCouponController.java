package com.lqzc.controller;

import com.lqzc.common.Result;
import com.lqzc.common.req.CouponTemplateCreateReq;
import com.lqzc.common.resp.CouponRecordResp;
import com.lqzc.common.PageResp;
import com.lqzc.common.domain.CouponTemplate;
import com.lqzc.service.CouponTemplateService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.Collections;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@Tag(name = "后台-优惠券管理")
@RestController
@RequestMapping("/admin/coupon")
@RequiredArgsConstructor
public class AdminCouponController {

    private final CouponTemplateService couponTemplateService;

    @Operation(summary = "创建优惠券模板")
    @PostMapping("/create")
    public Result<Void> create(@RequestBody CouponTemplateCreateReq req) {
        // TODO 保存模板
        return Result.success();
    }

    @Operation(summary = "优惠券模板列表")
    @GetMapping("/list")
    public Result<PageResp<CouponTemplate>> list(@RequestParam(defaultValue = "1") Integer current,
                                                 @RequestParam(defaultValue = "10") Integer size,
                                                 @RequestParam(required = false) Integer status,
                                                 @RequestParam(required = false) String title) {
        PageResp<CouponTemplate> page = new PageResp<>();
        page.setTotal(0L);
        page.setRecords(Collections.emptyList());
        return Result.success(page);
    }

    @Operation(summary = "优惠券上下架")
    @PutMapping("/status/{id}")
    public Result<Void> changeStatus(@PathVariable Long id, @RequestParam Integer status) {
        // TODO 更新模板状态
        return Result.success();
    }

    @Operation(summary = "优惠券发放记录")
    @GetMapping("/record/list")
    public Result<PageResp<CouponRecordResp>> records(@RequestParam(defaultValue = "1") Integer current,
                                                      @RequestParam(defaultValue = "10") Integer size,
                                                      @RequestParam(required = false) Long templateId,
                                                      @RequestParam(required = false) String customerPhone,
                                                      @RequestParam(required = false) Integer status) {
        PageResp<CouponRecordResp> page = new PageResp<>();
        page.setTotal(0L);
        page.setRecords(Collections.emptyList());
        return Result.success(page);
    }
}
