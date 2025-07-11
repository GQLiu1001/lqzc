package com.lqzc.mapper;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.OrderInfo;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.lqzc.common.records.DispatchOrderFetchRecords;
import com.lqzc.common.records.DispatchOrderListRecord;
import com.lqzc.common.records.OrderInfoRecords;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

/**
* @author 11965
* @description 针对表【order_info(订单主表)】的数据库操作Mapper
* @createDate 2025-07-11 09:05:49
* @Entity com.lqzc.common.domain.OrderInfo
*/
public interface OrderInfoMapper extends BaseMapper<OrderInfo> {
    @Select("select * from order_info")
    IPage<DispatchOrderListRecord> getList(IPage<DispatchOrderListRecord> pageNum);
    @Update("update order_info set dispatch_status = #{i} where order_no = #{orderNo}  ")
    int changeDispatchStatusByOrderNo(String orderNo, int i);
    @Select("select * from order_info where order_no = #{orderNo}")
    OrderInfo selectByOrderNo(String orderNo);

    IPage<OrderInfoRecords> getOrderList(IPage<OrderInfoRecords> page, String startStr, String endStr, String customerPhone);

    IPage<DispatchOrderFetchRecords> fetchDispatchOrder(IPage<DispatchOrderFetchRecords> page, Integer status, String startStr, String endStr, String customerPhone);

    IPage<DispatchOrderFetchRecords> fetchDispatchOrder4Driver(IPage<DispatchOrderFetchRecords> page, Integer status);
}




