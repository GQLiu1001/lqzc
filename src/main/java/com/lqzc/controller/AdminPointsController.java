package com.lqzc.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lqzc.common.Result;
import com.lqzc.common.req.PointsAdjustReq;
import com.lqzc.common.PageResp;
import com.lqzc.common.resp.PointsLogItemResp;
import com.lqzc.service.LoyaltyPointsLogService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 后台积分管理控制器
 * <p>
 * 提供积分管理的REST API接口，包括：
 * - 积分流水查询
 * - 人工调整积分
 * </p>
 *
 * @author rabbittank
 */
@Tag(name = "后台-积分管理")
@RestController
@RequestMapping("/admin/points")
@RequiredArgsConstructor
public class AdminPointsController {

    private final LoyaltyPointsLogService pointsLogService;

    /**
     * 分页查询积分流水
     *
     * @param current       当前页码，默认1
     * @param size          每页条数，默认10
     * @param customerPhone 客户手机号筛选，可选
     * @param sourceType    来源类型筛选，可选
     * @param dateRange     日期范围筛选（格式：2024-07-01,2024-07-31），可选
     * @return 流水分页数据
     */
    @Operation(summary = "积分流水查询")
    @GetMapping("/log/list")
    public Result<PageResp<PointsLogItemResp>> list(
            @Parameter(description = "当前页码") @RequestParam(defaultValue = "1") Integer current,
            @Parameter(description = "每页条数") @RequestParam(defaultValue = "10") Integer size,
            @Parameter(description = "客户手机号") @RequestParam(required = false) String customerPhone,
            @Parameter(description = "来源类型") @RequestParam(required = false) Integer sourceType,
            @Parameter(description = "日期范围") @RequestParam(required = false) String dateRange) {

        // 构建分页对象
        IPage<PointsLogItemResp> page = new Page<>(current, size);

        // 解析日期范围
        String startDate = null;
        String endDate = null;
        if (dateRange != null && dateRange.contains(",")) {
            String[] dates = dateRange.split(",");
            if (dates.length == 2) {
                startDate = dates[0].trim();
                endDate = dates[1].trim();
            }
        }

        // 调用Service层查询
        IPage<PointsLogItemResp> result = pointsLogService.getPointsLogList(page, customerPhone, sourceType, startDate, endDate);

        // 封装分页响应
        PageResp<PointsLogItemResp> resp = new PageResp<>();
        resp.setTotal(result.getTotal());
        resp.setRecords(result.getRecords());

        return Result.success(resp);
    }

    /**
     * 人工调整积分
     * <p>
     * 用于客服手动补偿或扣除积分。
     * </p>
     *
     * @param req 调整请求参数
     * @return 操作结果
     */
    @Operation(summary = "人工调整积分")
    @PostMapping("/adjust")
    public Result<Void> adjust(@RequestBody PointsAdjustReq req) {
        pointsLogService.adjustPoints(req);
        return Result.success();
    }
}
