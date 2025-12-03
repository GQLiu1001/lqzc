package com.lqzc.mapper;

import com.lqzc.common.domain.CustomerUser;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Param;

import java.util.Map;

/**
 * 客户用户Mapper接口
 * <p>
 * 提供客户用户表的数据库操作，包括：
 * - MyBatis-Plus提供的基础CRUD操作
 * - 自定义的复杂查询（如订单统计）
 * </p>
 *
 * @author rabbittank
 * @description 针对表【customer_user(前台客户账户)】的数据库操作Mapper
 * @createDate 2025-07-11 09:05:49
 * @Entity com.lqzc.common.domain.CustomerUser
 */
public interface CustomerUserMapper extends BaseMapper<CustomerUser> {

    /**
     * 查询客户的订单统计信息
     * <p>
     * 统计指定客户的订单数量和消费总额。
     * 只统计已完成的订单（order_status = 3）和已支付的订单（pay_status = 1）。
     * </p>
     *
     * @param customerId 客户ID
     * @return 包含统计结果的Map：
     *         - totalOrders: 总订单数（Integer）
     *         - totalSpent: 总消费金额（BigDecimal）
     *         如果客户没有订单记录，返回null或空Map
     */
    Map<String, Object> selectOrderStats(@Param("customerId") Long customerId);
}
