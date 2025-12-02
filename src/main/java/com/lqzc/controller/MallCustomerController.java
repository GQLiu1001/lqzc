package com.lqzc.controller;

import com.lqzc.common.Result;
import com.lqzc.common.exception.LianqingAdminException;
import com.lqzc.common.req.CustomerLoginReq;
import com.lqzc.common.req.CustomerProfileUpdateReq;
import com.lqzc.common.req.CustomerRegisterReq;
import com.lqzc.common.req.ForgotPasswordReq;
import com.lqzc.common.req.ResetPasswordReq;
import com.lqzc.common.resp.CustomerLoginResp;
import com.lqzc.common.resp.CustomerProfileResp;
import com.lqzc.service.CustomerUserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * C端客户账户控制器
 * <p>
 * 提供C端用户的登录、注册、个人信息管理等功能
 * </p>
 */
@Tag(name = "C端-客户账户")
@RestController
@RequestMapping("/mall/customer")
@RequiredArgsConstructor
public class MallCustomerController {

    private final CustomerUserService customerUserService;

    /**
     * 客户注册
     */
    @Operation(summary = "客户注册")
    @PostMapping("/register")
    public Result<Void> register(@RequestBody CustomerRegisterReq req) {
        customerUserService.register(req);
        return Result.success();
    }

    /**
     * 客户登录
     */
    @Operation(summary = "客户登录")
    @PostMapping("/login")
    public Result<CustomerLoginResp> login(@RequestBody CustomerLoginReq req) {
        CustomerLoginResp resp = customerUserService.login(req);
        return Result.success(resp);
    }

    /**
     * 客户登出
     */
    @Operation(summary = "客户登出")
    @PostMapping("/logout")
    public Result<Void> logout(@RequestHeader(value = "X-Customer-Token", required = false) String token) {
        customerUserService.logout(token);
        return Result.success();
    }

    /**
     * 获取个人信息
     * <p>
     * 需要在请求头中携带 X-Customer-Token
     * </p>
     */
    @Operation(summary = "获取个人信息")
    @GetMapping("/profile")
    public Result<CustomerProfileResp> profile(@RequestHeader(value = "X-Customer-Token", required = false) String token) {
        Long customerId = customerUserService.getCustomerIdByToken(token);
        if (customerId == null) {
            throw new LianqingAdminException("请先登录");
        }
        CustomerProfileResp resp = customerUserService.getProfile(customerId);
        return Result.success(resp);
    }

    /**
     * 修改个人信息
     * <p>
     * 需要在请求头中携带 X-Customer-Token
     * </p>
     */
    @Operation(summary = "修改个人信息")
    @PutMapping("/profile")
    public Result<Void> updateProfile(
            @RequestHeader(value = "X-Customer-Token", required = false) String token,
            @RequestBody CustomerProfileUpdateReq req) {
        Long customerId = customerUserService.getCustomerIdByToken(token);
        if (customerId == null) {
            throw new LianqingAdminException("请先登录");
        }
        customerUserService.updateProfile(customerId, req);
        return Result.success();
    }

    /**
     * 自助重置密码
     * <p>
     * 需要提供旧密码
     * </p>
     */
    @Operation(summary = "自助重置密码")
    @PostMapping("/reset-password")
    public Result<Void> resetPassword(@RequestBody ResetPasswordReq req) {
        customerUserService.resetPassword(req);
        return Result.success();
    }

    /**
     * 忘记密码（短信验证）
     * <p>
     * 简化实现：不校验短信验证码
     * </p>
     */
    @Operation(summary = "忘记密码（短信验证）")
    @PostMapping("/forgot-password")
    public Result<Void> forgotPassword(@RequestBody ForgotPasswordReq req) {
        customerUserService.forgotPassword(req);
        return Result.success();
    }
}
