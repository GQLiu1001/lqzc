package com.lqzc.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.OrderInfo;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.records.DispatchOrderFetchRecords;
import com.lqzc.common.records.DispatchOrderListRecord;
import com.lqzc.common.records.OrderInfoRecords;
import com.lqzc.common.req.OrderDispatchReq;
import com.lqzc.common.req.OrderNewReq;

/**
* @author 11965
* @description 针对表【order_info(订单主表)】的数据库操作Service
* @createDate 2025-07-11 09:05:49
*/
public interface OrderInfoService extends IService<OrderInfo> {

    IPage<OrderInfoRecords> getOrderList(IPage<OrderInfoRecords> page, Integer size, String startStr, String endStr, String customerPhone);

    void changeDispatchStatus(Long id, Integer status);
    
    /**
     * 更改派送状态并确认支付
     * @param id 订单ID
     * @param status 派送状态
     * @param payMethod 支付方式 wechat/alipay
     * @param couponId 优惠券ID（可选）
     */
    void changeDispatchStatusWithPayment(Long id, Integer status, String payMethod, Long couponId);

    void newOrder(OrderNewReq request);

    void newOrder(OrderNewReq request,String deliveryAddress);

    void dispatchOrder(OrderDispatchReq req);

    IPage<DispatchOrderFetchRecords> fetch(IPage<DispatchOrderFetchRecords> page, Integer status, String startTime, String endTime, String customerPhone);

    IPage<DispatchOrderListRecord> getList(IPage<DispatchOrderListRecord> pageNum);

    IPage<DispatchOrderFetchRecords> fetch(IPage<DispatchOrderFetchRecords> page, Integer status);

    Boolean robNewOrder(Long id, String orderNo);

    void changeOrderDispatchStatus(String orderNo, int i);
    
    /**
     * 确认收货并计算积分
     * @param orderId 订单ID
     * @param isAdmin 是否为后台操作
     */
    void confirmReceive(Long orderId, boolean isAdmin);
}
