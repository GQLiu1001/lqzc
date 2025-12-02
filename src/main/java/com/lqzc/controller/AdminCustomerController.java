package com.lqzc.controller;

import com.lqzc.common.Result;
import com.lqzc.common.req.AdminCustomerCreateReq;
import com.lqzc.common.req.AdminCustomerStatusReq;
import com.lqzc.common.resp.AdminCustomerDetailResp;
import com.lqzc.common.PageResp;
import com.lqzc.common.domain.CustomerUser;
import com.lqzc.service.CustomerUserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.Collections;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@Tag(name = "后台-客户管理")
@RestController
@RequestMapping("/admin/customer")
@RequiredArgsConstructor
public class AdminCustomerController {

    private final CustomerUserService customerUserService;

    @Operation(summary = "客户列表")
    @GetMapping("/list")
    public Result<PageResp<CustomerUser>> list(@RequestParam(defaultValue = "1") Integer current,
                                               @RequestParam(defaultValue = "10") Integer size,
                                               @RequestParam(required = false) String keyword,
                                               @RequestParam(required = false) Integer level,
                                               @RequestParam(required = false) Integer status) {
        PageResp<CustomerUser> page = new PageResp<>();
        page.setTotal(0L);
        page.setRecords(Collections.emptyList());
        return Result.success(page);
    }

    @Operation(summary = "后台创建客户")
    @PostMapping("/create")
    public Result<Void> create(@RequestBody AdminCustomerCreateReq req) {
        // TODO 创建客户
        return Result.success();
    }

    @Operation(summary = "客户详情")
    @GetMapping("/detail/{id}")
    public Result<AdminCustomerDetailResp> detail(@PathVariable Long id) {
        // TODO 查询详情
        return Result.success(new AdminCustomerDetailResp());
    }

    @Operation(summary = "更改客户状态")
    @PutMapping("/status/{id}")
    public Result<Void> changeStatus(@PathVariable Long id, @RequestBody AdminCustomerStatusReq req) {
        // TODO 更新状态
        return Result.success();
    }
}
