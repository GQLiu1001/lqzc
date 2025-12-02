package com.lqzc.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.lqzc.common.Result;
import com.lqzc.common.domain.CustomerUser;
import com.lqzc.service.CustomerUserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 客户通用接口控制器
 * <p>
 * 提供客户相关的通用API接口，如客户列表查询（用于创建订单等场景）
 * </p>
 */
@Tag(name = "客户通用接口")
@RestController
@RequestMapping("/customer")
@RequiredArgsConstructor
public class CustomerController {

    private final CustomerUserService customerUserService;

    /**
     * 查询客户列表（简化版，用于下拉选择）
     *
     * @param size    返回条数，默认100
     * @param keyword 搜索关键词（手机号或昵称）
     * @return 客户列表
     */
    @Operation(summary = "客户列表（简化版）")
    @GetMapping("/list")
    public Result<List<CustomerUser>> list(
            @Parameter(description = "返回条数") @RequestParam(defaultValue = "100") Integer size,
            @Parameter(description = "搜索关键词") @RequestParam(required = false) String keyword) {
        
        LambdaQueryWrapper<CustomerUser> wrapper = new LambdaQueryWrapper<>();
        
        // 关键词模糊搜索
        if (StringUtils.hasText(keyword)) {
            wrapper.and(w -> w
                    .like(CustomerUser::getPhone, keyword)
                    .or()
                    .like(CustomerUser::getNickname, keyword)
            );
        }
        
        // 只查询正常状态的客户
        wrapper.eq(CustomerUser::getStatus, 1);
        wrapper.orderByDesc(CustomerUser::getCreateTime);
        wrapper.last("LIMIT " + size);
        
        List<CustomerUser> list = customerUserService.list(wrapper);
        return Result.success(list);
    }
}

