package com.lqzc.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.domain.MemberLevel;
import com.lqzc.common.exception.LianqingAdminException;
import com.lqzc.common.req.MemberLevelSaveReq;
import com.lqzc.mapper.MemberLevelMapper;
import com.lqzc.service.MemberLevelService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.Date;

/**
 * 会员等级服务实现类
 *
 * @author 11965
 * @description 针对表【member_level(会员等级配置)】的数据库操作Service实现
 * @createDate 2025-12-02 00:00:00
 */
@Service
@RequiredArgsConstructor
public class MemberLevelServiceImpl extends ServiceImpl<MemberLevelMapper, MemberLevel>
        implements MemberLevelService {

    private final MemberLevelMapper memberLevelMapper;

    /**
     * 分页查询会员等级列表
     */
    @Override
    public IPage<MemberLevel> getMemberLevelList(IPage<MemberLevel> page) {
        LambdaQueryWrapper<MemberLevel> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByAsc(MemberLevel::getLevel);
        return memberLevelMapper.selectPage(page, wrapper);
    }

    /**
     * 新增或修改会员等级
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public void saveMemberLevel(MemberLevelSaveReq req) {
        // 1. 参数校验
        if (req.getLevel() == null) {
            throw new LianqingAdminException("等级编号不能为空");
        }
        if (!StringUtils.hasText(req.getName())) {
            throw new LianqingAdminException("等级名称不能为空");
        }

        // 2. 校验等级编号是否重复
        LambdaQueryWrapper<MemberLevel> checkWrapper = new LambdaQueryWrapper<>();
        checkWrapper.eq(MemberLevel::getLevel, req.getLevel());
        if (req.getId() != null) {
            checkWrapper.ne(MemberLevel::getId, req.getId());
        }
        Long count = memberLevelMapper.selectCount(checkWrapper);
        if (count > 0) {
            throw new LianqingAdminException("等级编号已存在");
        }

        // 3. 保存或更新
        MemberLevel memberLevel = new MemberLevel();
        BeanUtils.copyProperties(req, memberLevel);
        memberLevel.setUpdateTime(new Date());

        if (req.getId() == null) {
            // 新增
            memberLevel.setCreateTime(new Date());
            memberLevelMapper.insert(memberLevel);
        } else {
            // 更新
            memberLevelMapper.updateById(memberLevel);
        }
    }
}
