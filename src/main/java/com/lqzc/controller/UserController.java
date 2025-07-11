package com.lqzc.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lqzc.common.Result;
import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.records.UserListRecord;
import com.lqzc.common.req.UserChangeInfoReq;
import com.lqzc.common.resp.UserListResp;
import com.lqzc.common.resp.UserLoginResp;
import com.lqzc.utils.UserContextHolder;
import com.lqzc.aspect.LianqingLogin;
import com.lqzc.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.Resource;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.bind.annotation.*;

@Tag(name = "用户管理相关接口")
@RestController
@RequestMapping("/user")
public class UserController {
    @Resource
    private UserService userService;
    @Resource
    private StringRedisTemplate stringRedisTemplate;
    /**
     * 用户登录
     */
    @Operation(summary = "用户登录", description = "通过用户名和密码进行用户登录")
    @PostMapping("/login")
    public Result<UserLoginResp> login(@Parameter(description = "用户名", required = true) @RequestParam String username, 
                                      @Parameter(description = "密码", required = true) @RequestParam String password) {
        UserLoginResp resp = userService.login(username,password);
        return Result.success(resp);
    }
    
    /**
     * 用户注册
     */
    @Operation(summary = "用户注册", description = "注册新用户账号")
    @PostMapping("/register")
    public Result<?> register(@Parameter(description = "用户名", required = true) @RequestParam String username, 
                             @Parameter(description = "密码", required = true) @RequestParam String password, 
                             @Parameter(description = "手机号", required = true) @RequestParam String phone) {
        return userService.register(username,password,phone)?Result.success():Result.fail();
    }
    
    /**
     * 重置用户密码
     */
    @Operation(summary = "重置密码", description = "通过手机号重置用户密码")
    @PostMapping("/reset")
    public Result<?> reset(@Parameter(description = "用户名", required = true) @RequestParam String username, 
                          @Parameter(description = "手机号", required = true) @RequestParam String phone, 
                          @Parameter(description = "新密码", required = true) @RequestParam String new_password) {
        userService.reSetPassword(username,phone,new_password);
        return Result.success();
    }
    
    /**
     * 获取用户列表
     */
    @Operation(summary = "获取用户列表", description = "分页获取用户列表")
    @GetMapping("/list")
    public Result<UserListResp> list(@Parameter(description = "当前页码") @RequestParam(defaultValue = "1") Integer current, 
                                    @Parameter(description = "每页数量") @RequestParam(defaultValue = "10") Integer size) {
        IPage<UserListRecord> page = new Page<>(current, size);
        IPage<UserListRecord> record = userService.getUserList(page);
        UserListResp resp = new UserListResp();
        resp.setRecords(record.getRecords());
        resp.setTotal(record.getTotal());
        resp.setSize(record.getSize());
        resp.setCurrent(record.getCurrent());
        return Result.success(resp);
    }
    
    /**
     * 修改自己信息
     */
    @Operation(summary = "修改用户信息", description = "修改当前用户的个人信息")
    @PutMapping("/change-info")
    public Result<?> changeInfo(@Parameter(description = "用户信息修改请求", required = true) @RequestBody UserChangeInfoReq request) {
        userService.changeUserInfo(request);
        return Result.success();
    }
    
    /**
     * 删除id用户
     */
    @LianqingLogin
    @Operation(summary = "删除用户", description = "根据用户ID删除用户")
    @DeleteMapping("/delete/{id}")
    public Result<?> delete(@Parameter(description = "用户ID", required = true) @PathVariable Long id) {
        userService.removeById(id);
        return Result.success();
    }

    @Operation(summary = "用户登出")
    @GetMapping("/logout")
    public Result<?> logout() {
        String userToken = UserContextHolder.getUserToken();
        stringRedisTemplate.delete(RedisConstant.USER_TOKEN+userToken);
        return Result.success();
    }

}
