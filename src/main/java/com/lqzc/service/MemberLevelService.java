package com.lqzc.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.domain.MemberLevel;
import com.lqzc.common.req.MemberLevelSaveReq;

/**
 * 会员等级服务接口
 * <p>
 * 提供会员等级管理相关的业务操作，包括：
 * - 等级列表分页查询
 * - 新增/修改等级配置
 * </p>
 *
 * @author 11965
 * @description 针对表【member_level(会员等级配置)】的数据库操作Service
 * @createDate 2025-12-02 00:00:00
 */
public interface MemberLevelService extends IService<MemberLevel> {

    /**
     * 分页查询会员等级列表
     * <p>
     * 按等级从低到高排序。
     * </p>
     *
     * @param page 分页对象
     * @return 等级分页数据
     */
    IPage<MemberLevel> getMemberLevelList(IPage<MemberLevel> page);

    /**
     * 新增或修改会员等级
     * <p>
     * 如果id为空则新增，否则更新。
     * 会校验等级编号是否重复。
     * </p>
     *
     * @param req 保存请求参数
     * @throws com.lqzc.common.exception.LianqingAdminException 当等级编号重复时抛出
     */
    void saveMemberLevel(MemberLevelSaveReq req);
}
