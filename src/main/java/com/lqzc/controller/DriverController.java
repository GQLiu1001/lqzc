package com.lqzc.controller;

import com.lqzc.common.Result;
import com.lqzc.common.constant.DriverStatusConstant;
import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.resp.DriverInfoResp;
import com.lqzc.utils.UserContextHolder;
import com.lqzc.service.DriverService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.Resource;
import me.chanjar.weixin.common.error.WxErrorException;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;

@Tag(name = "派送系统司机认证相关接口")
@RestController
@RequestMapping("/driver")
public class DriverController {
    @Resource
    private DriverService driverService;
    @Resource
    private StringRedisTemplate stringRedisTemplate;
    /**
     * 司机登录
     */
    @Operation(summary = "司机登录", description = "司机通过验证码和手机号登录")
    @PostMapping("/login")
    public Result<DriverInfoResp> login(@Parameter(description = "验证码", required = true) @RequestParam String code, 
                                       @Parameter(description = "手机号", required = true) @RequestParam String phone) throws WxErrorException {
        DriverInfoResp resp = driverService.login(code,phone);
        return Result.success(resp);
    }
    
    /**
     * 获取司机审核状态
     */
    @Operation(summary = "获取司机审核状态", description = "查询司机账户的审核状态")
    @GetMapping("/audit-status/{id}")
    public Result<Integer> auditStatus(@Parameter(description = "司机ID", required = true) @PathVariable Long id) {
        Integer resp = driverService.auditStatus(id);
        return Result.success(resp);
    }
    
    /**
     * 司机登出
     */
    @Operation(summary = "司机登出", description = "司机退出登录")
    @GetMapping("/logout")
    public Result<?> logout() {
        String userToken = UserContextHolder.getUserToken();
        stringRedisTemplate.delete(RedisConstant.DRIVER_TOKEN+userToken);
        driverService.changeStatus(UserContextHolder.getDriverId(), DriverStatusConstant.OFFLINE);
        return Result.success();
    }

    /**
     * 更新司机状态
     */
    @Operation(summary = "更新司机状态", description = "更新司机的在线/离线状态")
    @PostMapping("/info/change-status/{id}/{status}")
    public Result<?> changeStatus(@Parameter(description = "司机ID", required = true) @PathVariable Long id, 
                                 @Parameter(description = "状态值", required = true) @PathVariable Integer status) {
        Integer resp = driverService.changeStatus(id,status);
        return resp == 0 ? Result.fail():Result.success();
    }
    
    /**
     * 获取钱包信息
     */
    @Operation(summary = "获取钱包信息", description = "查询司机的钱包余额")
    @GetMapping("/info/wallet/{id}")
    public Result<BigDecimal> wallet(@Parameter(description = "司机ID", required = true) @PathVariable Long id) {
        BigDecimal resp = driverService.wallet(id);
        return Result.success(resp);
    }
    
    /**
     * 更新司机经纬度地址
     */
    @Operation(summary = "更新司机经纬度地址", description = "更新司机的当前位置信息")
    @PostMapping("/info/update-location")
    public Result<?> updateLocation(@Parameter(description = "司机ID", required = true) @RequestParam Long id,
                                   @Parameter(description = "纬度", required = true) @RequestParam BigDecimal latitude,
                                   @Parameter(description = "经度", required = true) @RequestParam BigDecimal longitude) {
        driverService.updateLocation(id,latitude,longitude);
        return Result.success();
    }
}
