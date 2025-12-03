package com.lqzc.mapper;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.CouponTemplate;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.lqzc.common.resp.CouponTemplateListResp;
import org.apache.ibatis.annotations.Param;

/**
 * 优惠券模板Mapper接口
 * <p>
 * 提供优惠券模板表的数据库操作，包括：
 * - MyBatis-Plus提供的基础CRUD操作
 * - 自定义的复杂查询（如带统计的列表查询）
 * </p>
 *
 * @author rabbittank
 * @description 针对表【coupon_template(优惠券模板)】的数据库操作Mapper
 * @createDate 2025-07-11 09:05:49
 * @Entity com.lqzc.common.domain.CouponTemplate
 */
public interface CouponTemplateMapper extends BaseMapper<CouponTemplate> {

    /**
     * 分页查询优惠券模板列表（含统计信息）
     * <p>
     * 关联customer_coupon表统计：
     * - received_count: 已领取数量（该模板对应的所有券记录数）
     * - used_count: 已核销数量（该模板对应status=1的券记录数）
     * </p>
     *
     * @param page   分页对象
     * @param status 状态筛选（1=启用 0=停用），可为null
     * @param title  标题模糊搜索，可为null
     * @return 模板分页数据，包含统计信息
     */
    IPage<CouponTemplateListResp> selectTemplateListWithStats(
            IPage<CouponTemplateListResp> page,
            @Param("status") Integer status,
            @Param("title") String title
    );
}
