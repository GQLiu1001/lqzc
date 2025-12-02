package com.lqzc.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lqzc.common.Result;
import com.lqzc.common.req.AdminCustomerCreateReq;
import com.lqzc.common.req.AdminCustomerStatusReq;
import com.lqzc.common.resp.AdminCustomerDetailResp;
import com.lqzc.common.PageResp;
import com.lqzc.common.domain.CustomerAddress;
import com.lqzc.common.domain.CustomerUser;
import com.lqzc.service.CustomerAddressService;
import com.lqzc.service.CustomerUserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;

import java.util.Date;
import java.util.List;

/**
 * 后台客户管理控制器
 * <p>
 * 提供C端客户管理的REST API接口，包括：
 * - 客户列表分页查询
 * - 后台创建客户
 * - 客户详情查询
 * - 客户状态变更
 * </p>
 * <p>
 * 说明：Controller层只负责处理分页参数等与业务无关的代码，
 * 具体业务逻辑由Service层实现。
 * </p>
 *
 * @author lqzc
 */
@Tag(name = "后台-客户管理")
@RestController
@RequestMapping("/admin/customer")
@RequiredArgsConstructor
public class AdminCustomerController {

    private final CustomerUserService customerUserService;
    private final CustomerAddressService customerAddressService;

    /**
     * 分页查询客户列表
     * <p>
     * 支持按关键词（手机号或昵称）、会员等级、状态筛选。
     * 结果按创建时间倒序排列。
     * </p>
     *
     * @param current 当前页码，默认1
     * @param size    每页条数，默认10
     * @param keyword 搜索关键词（手机号或昵称），可选
     * @param level   会员等级筛选，可选
     * @param status  状态筛选（1正常 0停用），可选
     * @return 客户分页数据
     */
    @Operation(summary = "客户列表")
    @GetMapping("/list")
    public Result<PageResp<CustomerUser>> list(
            @Parameter(description = "当前页码") @RequestParam(defaultValue = "1") Integer current,
            @Parameter(description = "每页条数") @RequestParam(defaultValue = "10") Integer size,
            @Parameter(description = "搜索关键词（手机号或昵称）") @RequestParam(required = false) String keyword,
            @Parameter(description = "会员等级筛选") @RequestParam(required = false) Integer level,
            @Parameter(description = "状态筛选（1正常 0停用）") @RequestParam(required = false) Integer status) {

        // 构建分页对象
        IPage<CustomerUser> page = new Page<>(current, size);

        // 调用Service层进行业务查询
        IPage<CustomerUser> result = customerUserService.getCustomerList(page, keyword, level, status);

        // 封装分页响应
        PageResp<CustomerUser> resp = new PageResp<>();
        resp.setTotal(result.getTotal());
        resp.setRecords(result.getRecords());

        return Result.success(resp);
    }

    /**
     * 后台创建客户
     * <p>
     * 用于电话订单或线下客户录入场景。
     * 创建客户时会自动创建积分账户。
     * </p>
     *
     * @param req 创建客户请求参数
     * @return 操作结果
     */
    @Operation(summary = "后台创建客户")
    @PostMapping("/create")
    public Result<Void> create(@RequestBody AdminCustomerCreateReq req) {
        customerUserService.createCustomer(req);
        return Result.success();
    }

    /**
     * 查询客户详情
     * <p>
     * 返回客户的完整信息，包括基础信息、资产信息、统计数据。
     * </p>
     *
     * @param id 客户ID
     * @return 客户详情
     */
    @Operation(summary = "客户详情")
    @GetMapping("/detail/{id}")
    public Result<AdminCustomerDetailResp> detail(
            @Parameter(description = "客户ID") @PathVariable Long id) {
        AdminCustomerDetailResp resp = customerUserService.getCustomerDetail(id);
        return Result.success(resp);
    }

    /**
     * 更改客户状态
     * <p>
     * 用于冻结或解冻客户账号。
     * 冻结后客户将无法登录和下单。
     * </p>
     *
     * @param id  客户ID
     * @param req 状态变更请求（包含目标状态和变更原因）
     * @return 操作结果
     */
    @Operation(summary = "更改客户状态")
    @PutMapping("/status/{id}")
    public Result<Void> changeStatus(
            @Parameter(description = "客户ID") @PathVariable Long id,
            @RequestBody AdminCustomerStatusReq req) {
        customerUserService.changeCustomerStatus(id, req);
        return Result.success();
    }

    // ==================== 地址管理 API ====================

    /**
     * 获取客户地址列表
     *
     * @param phone      客户手机号（可选）
     * @param customerId 客户ID（可选）
     * @return 地址列表
     */
    @Operation(summary = "获取客户地址列表")
    @GetMapping("/address/list")
    public Result<List<CustomerAddress>> getAddressList(
            @Parameter(description = "客户手机号") @RequestParam(required = false) String phone,
            @Parameter(description = "客户ID") @RequestParam(required = false) Long customerId) {
        LambdaQueryWrapper<CustomerAddress> wrapper = new LambdaQueryWrapper<>();
        
        // 优先通过手机号查询
        if (StringUtils.hasText(phone)) {
            // 先通过手机号查找客户ID
            CustomerUser customer = customerUserService.lambdaQuery()
                    .eq(CustomerUser::getPhone, phone)
                    .one();
            if (customer != null) {
                wrapper.eq(CustomerAddress::getCustomerId, customer.getId());
            } else {
                return Result.success(List.of());
            }
        } else if (customerId != null) {
            wrapper.eq(CustomerAddress::getCustomerId, customerId);
        } else {
            return Result.success(List.of());
        }
        
        wrapper.orderByDesc(CustomerAddress::getIsDefault)
               .orderByDesc(CustomerAddress::getCreateTime);
        
        List<CustomerAddress> list = customerAddressService.list(wrapper);
        return Result.success(list);
    }

    /**
     * 添加客户地址
     * <p>
     * 如果设为默认地址，会先取消该客户其他地址的默认状态
     * </p>
     */
    @Operation(summary = "添加客户地址")
    @PostMapping("/address/add")
    public Result<Void> addAddress(@RequestBody CustomerAddress address) {
        // 如果设为默认，先取消该客户其他地址的默认状态
        if (address.getIsDefault() != null && address.getIsDefault() == 1) {
            clearOtherDefaultAddresses(address.getCustomerId(), null);
        }
        address.setCreateTime(new Date());
        address.setUpdateTime(new Date());
        customerAddressService.save(address);
        return Result.success();
    }

    /**
     * 更新客户地址
     * <p>
     * 如果设为默认地址，会先取消该客户其他地址的默认状态
     * </p>
     */
    @Operation(summary = "更新客户地址")
    @PutMapping("/address/update")
    public Result<Void> updateAddress(@RequestBody CustomerAddress address) {
        // 如果设为默认，先取消该客户其他地址的默认状态
        if (address.getIsDefault() != null && address.getIsDefault() == 1) {
            clearOtherDefaultAddresses(address.getCustomerId(), address.getId());
        }
        address.setUpdateTime(new Date());
        customerAddressService.updateById(address);
        return Result.success();
    }

    /**
     * 清除客户其他地址的默认状态
     *
     * @param customerId 客户ID
     * @param excludeId  排除的地址ID（更新时排除当前地址）
     */
    private void clearOtherDefaultAddresses(Long customerId, Long excludeId) {
        if (customerId == null) return;
        
        LambdaQueryWrapper<CustomerAddress> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(CustomerAddress::getCustomerId, customerId)
               .eq(CustomerAddress::getIsDefault, 1);
        if (excludeId != null) {
            wrapper.ne(CustomerAddress::getId, excludeId);
        }
        
        List<CustomerAddress> defaultAddresses = customerAddressService.list(wrapper);
        for (CustomerAddress addr : defaultAddresses) {
            addr.setIsDefault(0);
            addr.setUpdateTime(new Date());
            customerAddressService.updateById(addr);
        }
    }

    /**
     * 删除客户地址
     */
    @Operation(summary = "删除客户地址")
    @DeleteMapping("/address/delete/{id}")
    public Result<Void> deleteAddress(@PathVariable Long id) {
        customerAddressService.removeById(id);
        return Result.success();
    }
}
