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
* @author rabbittank
* @description 针对表【order_info(订单主表)】的数据库操作Service
* @createDate 2025-07-11 09:05:49
*/
public interface OrderInfoService extends IService<OrderInfo> {

    /**
     * 分页查询订单列表
     * <p>
     * 支持按日期范围和客户手机号筛选订单。
     * </p>
     *
     * @param page          分页对象
     * @param size          每页大小
     * @param startStr      开始日期字符串
     * @param endStr        结束日期字符串
     * @param customerPhone 客户手机号
     * @return 订单分页数据
     */
    IPage<OrderInfoRecords> getOrderList(IPage<OrderInfoRecords> page, Integer size, String startStr, String endStr, String customerPhone);

    /**
     * 更改订单派送状态
     *
     * @param id     订单ID
     * @param status 目标派送状态
     */
    void changeDispatchStatus(Long id, Integer status);
    
    /**
     * 更改派送状态并确认支付
     * @param id 订单ID
     * @param status 派送状态
     * @param payMethod 支付方式 wechat/alipay
     * @param couponId 优惠券ID（可选）
     */
    void changeDispatchStatusWithPayment(Long id, Integer status, String payMethod, Long couponId);

    /**
     * 创建新订单
     *
     * @param request 订单创建请求参数
     */
    void newOrder(OrderNewReq request);

    /**
     * 创建新订单（指定配送地址）
     *
     * @param request         订单创建请求参数
     * @param deliveryAddress 配送地址
     */
    void newOrder(OrderNewReq request, String deliveryAddress);

    /**
     * 派单操作
     * <p>
     * 为订单指派配送司机。
     * </p>
     *
     * @param req 派单请求参数
     */
    void dispatchOrder(OrderDispatchReq req);

    /**
     * 分页获取待派送订单
     * <p>
     * 支持按状态、时间范围和客户手机号筛选。
     * </p>
     *
     * @param page          分页对象
     * @param status        订单状态
     * @param startTime     开始时间
     * @param endTime       结束时间
     * @param customerPhone 客户手机号
     * @return 订单分页数据
     */
    IPage<DispatchOrderFetchRecords> fetch(IPage<DispatchOrderFetchRecords> page, Integer status, String startTime, String endTime, String customerPhone);

    /**
     * 分页获取派送订单列表
     *
     * @param pageNum 分页对象
     * @return 派送订单分页数据
     */
    IPage<DispatchOrderListRecord> getList(IPage<DispatchOrderListRecord> pageNum);

    /**
     * 分页获取待派送订单（按状态筛选）
     *
     * @param page   分页对象
     * @param status 订单状态
     * @return 订单分页数据
     */
    IPage<DispatchOrderFetchRecords> fetch(IPage<DispatchOrderFetchRecords> page, Integer status);

    /**
     * 司机抢单
     *
     * @param id      司机ID
     * @param orderNo 订单编号
     * @return 抢单是否成功
     */
    Boolean robNewOrder(Long id, String orderNo);

    /**
     * 更改订单派送状态（通过订单编号）
     *
     * @param orderNo 订单编号
     * @param i       目标状态
     */
    void changeOrderDispatchStatus(String orderNo, int i);
    
    /**
     * 确认收货并计算积分
     * @param orderId 订单ID
     * @param isAdmin 是否为后台操作
     */
    void confirmReceive(Long orderId, boolean isAdmin);
}
