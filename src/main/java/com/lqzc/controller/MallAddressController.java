package com.lqzc.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.lqzc.common.Result;
import com.lqzc.common.domain.CustomerAddress;
import com.lqzc.service.CustomerAddressService;
import com.lqzc.utils.UserContextHolder;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * C端收货地址管理控制器
 * <p>
 * 提供登录用户的收货地址增删改查功能
 * </p>
 */
@Tag(name = "C端-收货地址管理")
@RestController
@RequestMapping("/mall/address")
@RequiredArgsConstructor
public class MallAddressController {

    private final CustomerAddressService customerAddressService;

    @Operation(summary = "获取地址列表")
    @GetMapping("/list")
    public Result<List<CustomerAddress>> list() {
        Long customerId = UserContextHolder.getCustomerId();
        LambdaQueryWrapper<CustomerAddress> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(CustomerAddress::getCustomerId, customerId);
        queryWrapper.orderByDesc(CustomerAddress::getIsDefault);
        queryWrapper.orderByDesc(CustomerAddress::getCreateTime);
        List<CustomerAddress> addresses = customerAddressService.list(queryWrapper);
        return Result.success(addresses);
    }

    @Operation(summary = "新增收货地址")
    @PostMapping("/add")
    public Result<Void> add(@RequestBody CustomerAddress address) {
        Long customerId = UserContextHolder.getCustomerId();
        address.setCustomerId(customerId);
        
        // 如果设置为默认地址，需要清除其他默认地址
        if (address.getIsDefault() != null && address.getIsDefault() == 1) {
            clearOtherDefaultAddresses(customerId, null);
        }
        
        customerAddressService.save(address);
        return Result.success();
    }

    @Operation(summary = "修改收货地址")
    @PutMapping("/update")
    public Result<Void> update(@RequestBody CustomerAddress address) {
        Long customerId = UserContextHolder.getCustomerId();
        
        // 验证地址归属
        CustomerAddress existing = customerAddressService.getById(address.getId());
        if (existing == null || !existing.getCustomerId().equals(customerId)) {
            return Result.fail(500, "地址不存在或无权限修改", null);
        }
        
        address.setCustomerId(customerId);
        
        // 如果设置为默认地址，需要清除其他默认地址
        if (address.getIsDefault() != null && address.getIsDefault() == 1) {
            clearOtherDefaultAddresses(customerId, address.getId());
        }
        
        customerAddressService.updateById(address);
        return Result.success();
    }

    @Operation(summary = "删除收货地址")
    @DeleteMapping("/delete/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        Long customerId = UserContextHolder.getCustomerId();
        
        // 验证地址归属
        CustomerAddress existing = customerAddressService.getById(id);
        if (existing == null || !existing.getCustomerId().equals(customerId)) {
            return Result.fail(500, "地址不存在或无权限删除", null);
        }
        
        customerAddressService.removeById(id);
        return Result.success();
    }

    /**
     * 清除客户的其他默认地址
     *
     * @param customerId      客户ID
     * @param excludeAddressId 排除的地址ID（可为null）
     */
    private void clearOtherDefaultAddresses(Long customerId, Long excludeAddressId) {
        LambdaUpdateWrapper<CustomerAddress> updateWrapper = new LambdaUpdateWrapper<>();
        updateWrapper.eq(CustomerAddress::getCustomerId, customerId);
        updateWrapper.eq(CustomerAddress::getIsDefault, 1);
        if (excludeAddressId != null) {
            updateWrapper.ne(CustomerAddress::getId, excludeAddressId);
        }
        updateWrapper.set(CustomerAddress::getIsDefault, 0);
        customerAddressService.update(updateWrapper);
    }
}
