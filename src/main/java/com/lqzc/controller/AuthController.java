package com.lqzc.controller;


import com.lqzc.common.Result;
import com.lqzc.utils.JwtUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.Resource;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "商城系统匿名登录相关接口")
@RestController
@RequestMapping("/mall/auth")
public class AuthController {

    @Resource
    private JwtUtils jwtUtils;

    /**
     * JWT
     * @return
     */
    @Operation(summary = "获取匿名token")
    @GetMapping("/anonymous-token")
    public Result<String> anonymousToken() {
        return Result.success(jwtUtils.generateAnonymousToken());
    }
}
