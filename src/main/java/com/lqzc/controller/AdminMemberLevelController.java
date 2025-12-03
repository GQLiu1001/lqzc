package com.lqzc.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lqzc.common.Result;
import com.lqzc.common.domain.MemberLevel;
import com.lqzc.common.req.MemberLevelSaveReq;
import com.lqzc.common.PageResp;
import com.lqzc.service.MemberLevelService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 后台会员等级管理控制器
 * <p>
 * 提供会员等级管理的REST API接口，包括：
 * - 等级列表查询
 * - 新增/修改等级配置
 * </p>
 *
 * @author rabbittank
 */
@Tag(name = "后台-会员等级")
@RestController
@RequestMapping("/admin/member-level")
@RequiredArgsConstructor
public class AdminMemberLevelController {

    private final MemberLevelService memberLevelService;

    /**
     * 分页查询等级列表
     *
     * @param current 当前页码，默认1
     * @param size    每页条数，默认10
     * @return 等级分页数据
     */
    @Operation(summary = "等级列表")
    @GetMapping("/list")
    public Result<PageResp<MemberLevel>> list(
            @Parameter(description = "当前页码") @RequestParam(defaultValue = "1") Integer current,
            @Parameter(description = "每页条数") @RequestParam(defaultValue = "10") Integer size) {

        // 构建分页对象
        IPage<MemberLevel> page = new Page<>(current, size);

        // 调用Service层查询
        IPage<MemberLevel> result = memberLevelService.getMemberLevelList(page);

        // 封装分页响应
        PageResp<MemberLevel> resp = new PageResp<>();
        resp.setTotal(result.getTotal());
        resp.setRecords(result.getRecords());

        return Result.success(resp);
    }

    /**
     * 新增/修改等级
     * <p>
     * 如果id为空则新增，否则更新。
     * </p>
     *
     * @param req 保存请求参数
     * @return 操作结果
     */
    @Operation(summary = "新增/修改等级")
    @PostMapping("/save")
    public Result<Void> save(@RequestBody MemberLevelSaveReq req) {
        memberLevelService.saveMemberLevel(req);
        return Result.success();
    }
}
