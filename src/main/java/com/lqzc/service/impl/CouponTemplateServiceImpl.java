package com.lqzc.service.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.domain.CouponTemplate;
import com.lqzc.common.exception.LianqingAdminException;
import com.lqzc.common.req.CouponTemplateCreateReq;
import com.lqzc.common.resp.CouponRecordResp;
import com.lqzc.common.resp.CouponTemplateListResp;
import com.lqzc.mapper.CouponTemplateMapper;
import com.lqzc.mapper.CustomerCouponMapper;
import com.lqzc.service.CouponTemplateService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.Date;

/**
 * 优惠券模板服务实现类
 * <p>
 * 实现优惠券模板管理的核心业务逻辑，包括模板的创建、查询、
 * 状态管理以及发放记录查询等功能。
 * </p>
 *
 * @author 11965
 * @description 针对表【coupon_template(优惠券模板)】的数据库操作Service实现
 * @createDate 2025-07-11 09:05:49
 */
@Service
@RequiredArgsConstructor
public class CouponTemplateServiceImpl extends ServiceImpl<CouponTemplateMapper, CouponTemplate>
        implements CouponTemplateService {

    private final CouponTemplateMapper couponTemplateMapper;
    private final CustomerCouponMapper customerCouponMapper;

    /**
     * 创建优惠券模板
     * <p>
     * 业务流程：
     * 1. 校验必填参数（标题、类型、有效期）
     * 2. 根据优惠券类型校验对应字段
     * 3. 设置默认值（状态默认启用）
     * 4. 保存模板到数据库
     * </p>
     *
     * @param req 创建请求参数
     * @throws LianqingAdminException 当参数校验失败时抛出
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public void createTemplate(CouponTemplateCreateReq req) {
        // 调试日志
        System.out.println("========== 创建优惠券模板 ==========");
        System.out.println("请求参数: " + req);
        System.out.println("validFrom: " + req.getValidFrom());
        System.out.println("validTo: " + req.getValidTo());
        
        // 1. 基础参数校验
        if (!StringUtils.hasText(req.getTitle())) {
            throw new LianqingAdminException("优惠券标题不能为空");
        }
        if (req.getType() == null || req.getType() < 1 || req.getType() > 3) {
            throw new LianqingAdminException("优惠券类型无效，必须为1(满减)、2(折扣)或3(现金)");
        }
        if (req.getValidFrom() == null || req.getValidTo() == null) {
            throw new LianqingAdminException("有效期不能为空");
        }
        if (req.getValidFrom().after(req.getValidTo())) {
            throw new LianqingAdminException("有效期开始时间不能晚于结束时间");
        }
        if (req.getTotalIssued() == null || req.getTotalIssued() <= 0) {
            throw new LianqingAdminException("发行总量必须大于0");
        }

        // 2. 根据类型校验对应字段
        switch (req.getType()) {
            case 1: // 满减券
                if (req.getThresholdAmount() == null) {
                    throw new LianqingAdminException("满减券必须设置使用门槛");
                }
                if (req.getDiscountAmount() == null) {
                    throw new LianqingAdminException("满减券必须设置立减金额");
                }
                break;
            case 2: // 折扣券
                if (req.getDiscountRate() == null) {
                    throw new LianqingAdminException("折扣券必须设置折扣率");
                }
                break;
            case 3: // 现金券
                if (req.getDiscountAmount() == null) {
                    throw new LianqingAdminException("现金券必须设置金额");
                }
                break;
            default:
                throw new LianqingAdminException("不支持的优惠券类型");
        }

        // 3. 构建实体并设置默认值
        CouponTemplate template = new CouponTemplate();
        BeanUtils.copyProperties(req, template);
        // 默认状态为启用
        template.setStatus(1);
        // 每人限领默认为1
        if (template.getPerUserLimit() == null) {
            template.setPerUserLimit(1);
        }
        template.setCreateTime(new Date());
        template.setUpdateTime(new Date());

        // 4. 保存模板
        couponTemplateMapper.insert(template);
    }

    /**
     * 分页查询优惠券模板列表
     * <p>
     * 使用关联查询统计每个模板的领取数量和使用数量。
     * 通过CustomerCoupon表进行统计：
     * - received_count: 该模板的总领取数（COUNT）
     * - used_count: 该模板status=1的券数量
     * </p>
     *
     * @param page   分页对象
     * @param status 状态筛选
     * @param title  标题模糊搜索
     * @return 模板分页数据
     */
    @Override
    public IPage<CouponTemplateListResp> getTemplateList(IPage<CouponTemplateListResp> page, Integer status, String title) {
        // 调用Mapper的自定义XML查询，关联统计领取和使用数量
        return couponTemplateMapper.selectTemplateListWithStats(page, status, title);
    }

    /**
     * 变更优惠券模板状态
     * <p>
     * 更新模板的status字段，用于上架或下架优惠券。
     * 下架后新用户无法领取，但已领取的券不受影响。
     * </p>
     *
     * @param templateId 模板ID
     * @param status     目标状态
     * @throws LianqingAdminException 当模板不存在时抛出
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public void changeTemplateStatus(Long templateId, Integer status) {
        // 1. 校验模板是否存在
        CouponTemplate template = couponTemplateMapper.selectById(templateId);
        if (template == null) {
            throw new LianqingAdminException("优惠券模板不存在");
        }

        // 2. 校验状态值有效性
        if (status == null || (status != 0 && status != 1)) {
            throw new LianqingAdminException("状态值无效，必须为0(停用)或1(启用)");
        }

        // 3. 更新状态
        CouponTemplate updateTemplate = new CouponTemplate();
        updateTemplate.setId(templateId);
        updateTemplate.setStatus(status);
        updateTemplate.setUpdateTime(new Date());
        couponTemplateMapper.updateById(updateTemplate);
    }

    /**
     * 分页查询优惠券发放记录
     * <p>
     * 查询customer_coupon表，关联customer_user表获取手机号。
     * 支持多条件筛选：
     * - 模板ID精确匹配
     * - 客户手机号精确匹配
     * - 使用状态精确匹配
     * </p>
     *
     * @param page          分页对象
     * @param templateId    模板ID筛选
     * @param customerPhone 客户手机号筛选
     * @param status        使用状态筛选
     * @return 发放记录分页数据
     */
    @Override
    public IPage<CouponRecordResp> getCouponRecordList(IPage<CouponRecordResp> page, Long templateId, String customerPhone, Integer status) {
        // 调用Mapper的自定义XML查询，关联customer_user表获取手机号
        return customerCouponMapper.selectCouponRecordList(page, templateId, customerPhone, status);
    }
}
