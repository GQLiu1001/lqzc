package com.lqzc.controller;

import com.lqzc.common.Result;
import com.lqzc.common.req.AddressAddReq;
import com.lqzc.common.req.AddressUpdateReq;
import com.lqzc.common.domain.CustomerAddress;
import com.lqzc.service.CustomerAddressService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.Collections;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@Tag(name = "C端-收货地址")
@RestController
@RequestMapping("/mall/address")
@RequiredArgsConstructor
public class MallAddressController {

    private final CustomerAddressService customerAddressService;

    @Operation(summary = "获取地址列表")
    @GetMapping("/list")
    public Result<List<CustomerAddress>> list() {
        // TODO 查询当前用户地址
        return Result.success(Collections.emptyList());
    }

    @Operation(summary = "新增收货地址")
    @PostMapping("/add")
    public Result<Void> add(@RequestBody AddressAddReq req) {
        // TODO 保存地址
        return Result.success();
    }

    @Operation(summary = "修改收货地址")
    @PutMapping("/update")
    public Result<Void> update(@RequestBody AddressUpdateReq req) {
        // TODO 更新地址
        return Result.success();
    }

    @Operation(summary = "删除收货地址")
    @DeleteMapping("/delete/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        // TODO 删除地址
        return Result.success();
    }
}
