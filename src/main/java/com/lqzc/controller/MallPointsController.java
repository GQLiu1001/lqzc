package com.lqzc.controller;

import com.lqzc.common.Result;
import com.lqzc.common.PageResp;
import com.lqzc.common.resp.PointsLogItemResp;
import com.lqzc.common.resp.PointsOverviewResp;
import com.lqzc.service.LoyaltyPointsAccountService;
import com.lqzc.service.LoyaltyPointsLogService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.Collections;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "C端-积分")
@RestController
@RequestMapping("/mall/points")
@RequiredArgsConstructor
public class MallPointsController {

    private final LoyaltyPointsAccountService pointsAccountService;
    private final LoyaltyPointsLogService pointsLogService;

    @Operation(summary = "积分概览")
    @GetMapping("/overview")
    public Result<PointsOverviewResp> overview() {
        // TODO 查询积分账户
        return Result.success(new PointsOverviewResp());
    }

    @Operation(summary = "积分流水")
    @GetMapping("/logs")
    public Result<PageResp<PointsLogItemResp>> logs(@RequestParam(defaultValue = "1") Integer current,
                                                    @RequestParam(defaultValue = "10") Integer size) {
        // TODO 分页查询流水
        PageResp<PointsLogItemResp> page = new PageResp<>();
        page.setTotal(0L);
        page.setRecords(Collections.emptyList());
        return Result.success(page);
    }
}
