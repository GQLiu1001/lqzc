package com.lqzc.controller;

import com.lqzc.common.Result;
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

@Tag(name = "C端-客户账户")
@RestController
@RequestMapping("/mall/customer")
@RequiredArgsConstructor
public class MallCustomerController {

    private final CustomerUserService customerUserService;

    @Operation(summary = "客户注册")
    @PostMapping("/register")
    public Result<Void> register(@RequestBody CustomerRegisterReq req) {
        // TODO 调用 customerUserService 处理注册
        return Result.success();
    }

    @Operation(summary = "客户登录")
    @PostMapping("/login")
    public Result<CustomerLoginResp> login(@RequestBody CustomerLoginReq req) {
        // TODO 调用 customerUserService 处理登录
        return Result.success(new CustomerLoginResp());
    }

    @Operation(summary = "获取个人信息")
    @GetMapping("/profile")
    public Result<CustomerProfileResp> profile() {
        // TODO 查询用户信息
        return Result.success(new CustomerProfileResp());
    }

    @Operation(summary = "修改个人信息")
    @PutMapping("/profile")
    public Result<Void> updateProfile(@RequestBody CustomerProfileUpdateReq req) {
        // TODO 更新用户资料
        return Result.success();
    }

    @Operation(summary = "自助重置密码")
    @PostMapping("/reset-password")
    public Result<Void> resetPassword(@RequestBody ResetPasswordReq req) {
        // TODO 校验旧密码并更新
        return Result.success();
    }

    @Operation(summary = "忘记密码（短信验证）")
    @PostMapping("/forgot-password")
    public Result<Void> forgotPassword(@RequestBody ForgotPasswordReq req) {
        // TODO 校验短信验证码并更新密码
        return Result.success();
    }
}
