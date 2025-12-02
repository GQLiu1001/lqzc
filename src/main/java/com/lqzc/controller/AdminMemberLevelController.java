package com.lqzc.controller;

import com.lqzc.common.Result;
import com.lqzc.common.domain.MemberLevel;
import com.lqzc.common.req.MemberLevelSaveReq;
import com.lqzc.common.PageResp;
import com.lqzc.service.MemberLevelService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.Collections;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@Tag(name = "后台-会员等级")
@RestController
@RequestMapping("/admin/member-level")
@RequiredArgsConstructor
public class AdminMemberLevelController {

    private final MemberLevelService memberLevelService;

    @Operation(summary = "等级列表")
    @GetMapping("/list")
    public Result<PageResp<MemberLevel>> list(@RequestParam(defaultValue = "1") Integer current,
                                              @RequestParam(defaultValue = "10") Integer size) {
        PageResp<MemberLevel> page = new PageResp<>();
        page.setTotal(0L);
        page.setRecords(Collections.emptyList());
        return Result.success(page);
    }

    @Operation(summary = "新增/修改等级")
    @PostMapping("/save")
    public Result<Void> save(@RequestBody MemberLevelSaveReq req) {
        // TODO 保存或更新等级
        return Result.success();
    }
}
