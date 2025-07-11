package com.lqzc.service;

import com.lqzc.common.domain.OrderDetail;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.resp.SalesTrendResp;

import java.util.List;

/**
* @author 11965
* @description 针对表【order_detail(订单项表)】的数据库操作Service
* @createDate 2025-07-11 09:05:49
*/
public interface OrderDetailService extends IService<OrderDetail> {
    List<SalesTrendResp> topSalesTrend(Integer year, Integer month, Integer length);

//    List<SalesTrendResp> topSalesTrendMul(Integer year, Integer month, Integer length);

    void changeSubDetail(OrderDetail orderDetail, Integer changeType);
}
