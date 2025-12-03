package com.lqzc.service;

import com.lqzc.common.domain.OrderDetail;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.resp.SalesTrendResp;

import java.util.List;

/**
* @author rabbittank
* @description 针对表【order_detail(订单项表)】的数据库操作Service
* @createDate 2025-07-11 09:05:49
*/
public interface OrderDetailService extends IService<OrderDetail> {

    /**
     * 获取销售趋势数据
     * <p>
     * 统计指定年月的销售趋势数据。
     * </p>
     *
     * @param year   年份
     * @param month  月份
     * @param length 数据长度
     * @return 销售趋势响应列表
     */
    List<SalesTrendResp> topSalesTrend(Integer year, Integer month, Integer length);

//    List<SalesTrendResp> topSalesTrendMul(Integer year, Integer month, Integer length);

    /**
     * 修改订单明细
     * <p>
     * 根据变更类型调整订单明细信息。
     * </p>
     *
     * @param orderDetail 订单明细对象
     * @param changeType  变更类型
     */
    void changeSubDetail(OrderDetail orderDetail, Integer changeType);
}
