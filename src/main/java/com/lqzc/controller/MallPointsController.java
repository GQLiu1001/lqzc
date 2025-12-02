package com.lqzc.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lqzc.common.Result;
import com.lqzc.common.PageResp;
import com.lqzc.common.domain.LoyaltyPointsAccount;
import com.lqzc.common.domain.LoyaltyPointsLog;
import com.lqzc.common.resp.PointsLogItemResp;
import com.lqzc.common.resp.PointsOverviewResp;
import com.lqzc.service.LoyaltyPointsAccountService;
import com.lqzc.service.LoyaltyPointsLogService;
import com.lqzc.utils.UserContextHolder;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.text.SimpleDateFormat;
import java.util.List;
import java.util.stream.Collectors;

/**
 * C端积分控制器
 * <p>
 * 提供登录用户的积分概览和流水查询功能
 * </p>
 */
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
        Long customerId = UserContextHolder.getCustomerId();
        
        // 查询积分账户
        LambdaQueryWrapper<LoyaltyPointsAccount> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(LoyaltyPointsAccount::getCustomerId, customerId);
        LoyaltyPointsAccount account = pointsAccountService.getOne(queryWrapper);
        
        PointsOverviewResp resp = new PointsOverviewResp();
        if (account != null) {
            resp.setBalance(account.getBalance() != null ? account.getBalance() : 0);
            resp.setFrozen(account.getFrozen() != null ? account.getFrozen() : 0);
            resp.setTotalEarned(account.getTotalEarned() != null ? account.getTotalEarned() : 0);
            resp.setTotalSpent(account.getTotalSpent() != null ? account.getTotalSpent() : 0);
        } else {
            // 如果没有积分账户，返回默认值
            resp.setBalance(0);
            resp.setFrozen(0);
            resp.setTotalEarned(0);
            resp.setTotalSpent(0);
        }
        
        return Result.success(resp);
    }

    @Operation(summary = "积分流水")
    @GetMapping("/logs")
    public Result<PageResp<PointsLogItemResp>> logs(@RequestParam(defaultValue = "1") Integer current,
                                                    @RequestParam(defaultValue = "10") Integer size) {
        Long customerId = UserContextHolder.getCustomerId();
        
        // 分页查询流水
        LambdaQueryWrapper<LoyaltyPointsLog> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(LoyaltyPointsLog::getCustomerId, customerId);
        queryWrapper.orderByDesc(LoyaltyPointsLog::getCreateTime);
        
        Page<LoyaltyPointsLog> page = new Page<>(current, size);
        Page<LoyaltyPointsLog> logPage = pointsLogService.page(page, queryWrapper);
        
        // 转换为响应DTO
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        List<PointsLogItemResp> records = logPage.getRecords().stream()
                .map(log -> {
                    PointsLogItemResp item = new PointsLogItemResp();
                    item.setId(log.getId());
                    item.setChangeAmount(log.getChangeAmount());
                    item.setBalanceAfter(log.getBalanceAfter());
                    item.setSourceType(log.getSourceType());
                    item.setRemark(log.getRemark());
                    item.setCreateTime(log.getCreateTime() != null ? sdf.format(log.getCreateTime()) : null);
                    return item;
                })
                .collect(Collectors.toList());
        
        PageResp<PointsLogItemResp> resp = new PageResp<>();
        resp.setTotal(logPage.getTotal());
        resp.setRecords(records);
        
        return Result.success(resp);
    }
}
