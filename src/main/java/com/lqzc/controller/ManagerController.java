package com.lqzc.controller;

import com.lqzc.common.Result;
import com.lqzc.common.constant.DriverAuditStatusConstant;
import com.lqzc.common.domain.Driver;
import com.lqzc.common.resp.DriverListResp;
import com.lqzc.aspect.LianqingLogin;
import com.lqzc.service.DriverService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.Resource;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "管理员司机管理相关接口")
@RestController
@RequestMapping("/manager")
public class ManagerController {
    @Resource
    private DriverService driverService;

    /**
     * 获取司机列表
     */
    @Operation(summary = "获取司机列表", description = "获取所有司机的列表信息")
    @GetMapping("/driver-list")
    public Result<DriverListResp> driverList() {
        List<Driver> list = driverService.getDriverList();
        DriverListResp resp = new DriverListResp();
        resp.setRecords(list);
        resp.setTotal((long) list.size());
        return Result.success(resp);
    }
    
    /**
     * 同意司机资格
     */
    @LianqingLogin
    @Operation(summary = "同意司机资格", description = "批准司机的入驻申请")
    @PutMapping("/driver-approval/{id}")
    public Result<?> driverApproval(@Parameter(description = "司机ID", required = true) @PathVariable Long id) {
        driverService.auditDriverWithStatus(id, DriverAuditStatusConstant.PASS);
        return Result.success();
    }
    
    /**
     * 拒绝司机资格
     */
    @LianqingLogin
    @Operation(summary = "拒绝司机资格", description = "拒绝司机的入驻申请")
    @PutMapping("/driver-rejection/{id}")
    public Result<?> driverRejection(@Parameter(description = "司机ID", required = true) @PathVariable Long id) {
        driverService.auditDriverWithStatus(id,DriverAuditStatusConstant.REJECT);
        return Result.success();
    }
    
    /**
     * 删除司机
     */
    @LianqingLogin
    @Operation(summary = "删除司机", description = "删除指定司机账户")
    @DeleteMapping("/driver-delete/{id}")
    public Result<?> driverDelete(@Parameter(description = "司机ID", required = true) @PathVariable Long id) {
        driverService.removeById(id);
        return Result.success();
    }
    
    /**
     * 清零司机钱包
     */
    @LianqingLogin
    @Operation(summary = "清零司机钱包", description = "将指定司机的钱包余额清零")
    @DeleteMapping("/driver-reset-money/{id}")
    public Result<?> driverResetMoney(@Parameter(description = "司机ID", required = true) @PathVariable Long id) {
        driverService.driverResetMoney(id);
        return Result.success();
    }
}
