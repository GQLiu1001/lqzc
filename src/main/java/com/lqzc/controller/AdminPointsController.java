package com.lqzc.controller;

import com.lqzc.common.Result;
import com.lqzc.common.req.PointsAdjustReq;
import com.lqzc.common.PageResp;
import com.lqzc.common.resp.PointsLogItemResp;
import com.lqzc.service.LoyaltyPointsLogService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.Collections;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "后台-积分管理")
@RestController
@RequestMapping("/admin/points")
@RequiredArgsConstructor
public class AdminPointsController {

    private final LoyaltyPointsLogService pointsLogService;

    @Operation(summary = "积分流水查询")
    @GetMapping("/log/list")
    public Result<PageResp<PointsLogItemResp>> list(@RequestParam(defaultValue = "1") Integer current,
                                                    @RequestParam(defaultValue = "10") Integer size,
                                                    @RequestParam(required = false) String customerPhone,
                                                    @RequestParam(required = false) Integer sourceType,
                                                    @RequestParam(required = false) String dateRange) {
        PageResp<PointsLogItemResp> page = new PageResp<>();
        page.setTotal(0L);
        page.setRecords(Collections.emptyList());
        return Result.success(page);
    }

    @Operation(summary = "人工调整积分")
    @PostMapping("/adjust")
    public Result<Void> adjust(@RequestBody PointsAdjustReq req) {
        // TODO 调整积分
        return Result.success();
    }
}
