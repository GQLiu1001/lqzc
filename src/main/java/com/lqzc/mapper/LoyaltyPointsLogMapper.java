package com.lqzc.mapper;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.LoyaltyPointsLog;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.lqzc.common.resp.PointsLogItemResp;
import org.apache.ibatis.annotations.Param;

/**
 * 积分流水Mapper接口
 *
 * @author 11965
 * @description 针对表【loyalty_points_log(客户积分流水)】的数据库操作Mapper
 * @createDate 2025-07-11 09:05:49
 * @Entity com.lqzc.common.domain.LoyaltyPointsLog
 */
public interface LoyaltyPointsLogMapper extends BaseMapper<LoyaltyPointsLog> {

    /**
     * 分页查询积分流水列表（关联客户手机号）
     */
    IPage<PointsLogItemResp> selectPointsLogList(
            IPage<PointsLogItemResp> page,
            @Param("customerPhone") String customerPhone,
            @Param("sourceType") Integer sourceType,
            @Param("startDate") String startDate,
            @Param("endDate") String endDate
    );
}
