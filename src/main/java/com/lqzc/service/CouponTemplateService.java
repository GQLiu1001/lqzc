package com.lqzc.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.CouponTemplate;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.req.CouponTemplateCreateReq;
import com.lqzc.common.resp.CouponRecordResp;
import com.lqzc.common.resp.CouponTemplateListResp;

/**
 * 优惠券模板服务接口
 * <p>
 * 提供优惠券模板管理相关的业务操作，包括：
 * - 创建优惠券模板
 * - 分页查询模板列表（含领取/核销统计）
 * - 模板上下架状态管理
 * - 查询优惠券发放记录
 * </p>
 *
 * @author rabbittank
 * @description 针对表【coupon_template(优惠券模板)】的数据库操作Service
 * @createDate 2025-07-11 09:05:49
 */
public interface CouponTemplateService extends IService<CouponTemplate> {

    /**
     * 创建优惠券模板
     * <p>
     * 创建新的优惠券活动模板。
     * 创建后默认状态为启用（status=1）。
     * </p>
     *
     * @param req 创建请求参数，包含标题、类型、门槛金额、优惠金额/折扣率、发行量等
     * @throws com.lqzc.common.exception.LianqingAdminException 当参数校验失败时抛出
     */
    void createTemplate(CouponTemplateCreateReq req);

    /**
     * 分页查询优惠券模板列表
     * <p>
     * 查询优惠券模板信息，并统计每个模板的：
     * - 已领取数量（received_count）
     * - 已核销数量（used_count，即status=1的券数量）
     * 支持按标题模糊搜索和状态筛选。
     * </p>
     *
     * @param page   分页对象，包含当前页码和每页条数
     * @param status 状态筛选（1=启用 0=停用），可为null表示不筛选
     * @param title  标题模糊搜索，可为null表示不筛选
     * @return 模板分页数据，包含统计信息
     */
    IPage<CouponTemplateListResp> getTemplateList(IPage<CouponTemplateListResp> page, Integer status, String title);

    /**
     * 变更优惠券模板状态
     * <p>
     * 用于上架或下架优惠券模板。
     * 下架后用户无法继续领取该券，但已领取的券仍可使用。
     * </p>
     *
     * @param templateId 模板ID
     * @param status     目标状态（0=停用 1=启用）
     * @throws com.lqzc.common.exception.LianqingAdminException 当模板不存在时抛出
     */
    void changeTemplateStatus(Long templateId, Integer status);

    /**
     * 分页查询优惠券发放记录
     * <p>
     * 查询客户领取优惠券的详细记录。
     * 支持按模板ID、客户手机号、使用状态进行筛选。
     * </p>
     *
     * @param page          分页对象
     * @param templateId    模板ID筛选，可为null
     * @param customerPhone 客户手机号筛选，可为null
     * @param status        使用状态筛选（0未使用 1已使用 2过期 3作废），可为null
     * @return 发放记录分页数据
     */
    IPage<CouponRecordResp> getCouponRecordList(IPage<CouponRecordResp> page, Long templateId, String customerPhone, Integer status);
}
