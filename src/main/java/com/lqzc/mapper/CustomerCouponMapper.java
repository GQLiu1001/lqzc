package com.lqzc.mapper;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.CustomerCoupon;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.lqzc.common.resp.CouponRecordResp;
import org.apache.ibatis.annotations.Param;

/**
 * 客户优惠券Mapper接口
 * <p>
 * 提供客户优惠券表的数据库操作，包括：
 * - MyBatis-Plus提供的基础CRUD操作
 * - 自定义的复杂查询（如发放记录查询）
 * </p>
 *
 * @author rabbittank
 * @description 针对表【customer_coupon(客户优惠券)】的数据库操作Mapper
 * @createDate 2025-07-11 09:05:49
 * @Entity com.lqzc.common.domain.CustomerCoupon
 */
public interface CustomerCouponMapper extends BaseMapper<CustomerCoupon> {

    /**
     * 分页查询优惠券发放记录
     * <p>
     * 关联customer_user表获取客户手机号。
     * 支持多条件筛选：
     * - 模板ID精确匹配
     * - 客户手机号精确匹配
     * - 使用状态精确匹配（0未使用 1已使用 2过期 3作废）
     * </p>
     *
     * @param page          分页对象
     * @param templateId    模板ID，可为null
     * @param customerPhone 客户手机号，可为null
     * @param status        使用状态，可为null
     * @return 发放记录分页数据
     */
    IPage<CouponRecordResp> selectCouponRecordList(
            IPage<CouponRecordResp> page,
            @Param("templateId") Long templateId,
            @Param("customerPhone") String customerPhone,
            @Param("status") Integer status
    );
}
