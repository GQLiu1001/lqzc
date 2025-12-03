package com.lqzc.mapper;

import com.lqzc.common.domain.OrderDetail;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.lqzc.common.resp.SalesTrendResp;

/**
* @author rabbittank
* @description 针对表【order_detail(订单项表)】的数据库操作Mapper
* @createDate 2025-07-11 09:05:49
* @Entity com.lqzc.common.domain.OrderDetail
*/
public interface OrderDetailMapper extends BaseMapper<OrderDetail> {
    SalesTrendResp getTopSalesTrend(String date);
}




