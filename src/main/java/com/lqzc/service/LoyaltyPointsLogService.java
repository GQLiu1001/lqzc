package com.lqzc.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.LoyaltyPointsLog;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.req.PointsAdjustReq;
import com.lqzc.common.resp.PointsLogItemResp;

/**
 * 积分流水服务接口
 * <p>
 * 提供积分流水管理相关的业务操作，包括：
 * - 流水记录分页查询（支持手机号、来源类型、日期范围筛选）
 * - 人工调整积分
 * </p>
 *
 * @author rabbittank
 * @description 针对表【loyalty_points_log(客户积分流水)】的数据库操作Service
 * @createDate 2025-07-11 09:05:49
 */
public interface LoyaltyPointsLogService extends IService<LoyaltyPointsLog> {

    /**
     * 分页查询积分流水记录
     * <p>
     * 关联customer_user表获取客户手机号。
     * 支持多条件筛选：
     * - 客户手机号精确匹配
     * - 来源类型精确匹配
     * - 日期范围筛选
     * </p>
     *
     * @param page          分页对象
     * @param customerPhone 客户手机号，可为null
     * @param sourceType    来源类型（1下单赠送 2退款回退 3支付抵扣），可为null
     * @param startDate     开始日期，可为null
     * @param endDate       结束日期，可为null
     * @return 流水分页数据
     */
    IPage<PointsLogItemResp> getPointsLogList(IPage<PointsLogItemResp> page, String customerPhone, Integer sourceType, String startDate, String endDate);

    /**
     * 人工调整积分
     * <p>
     * 用于客服手动补偿或扣除积分。
     * 会同时更新积分账户余额和创建流水记录。
     * </p>
     *
     * @param req 调整请求，包含客户ID、变动积分、备注
     * @throws com.lqzc.common.exception.LianqingAdminException 当客户不存在或积分不足时抛出
     */
    void adjustPoints(PointsAdjustReq req);
}
