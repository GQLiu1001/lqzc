package com.lqzc.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.constant.DispatchConstant;
import com.lqzc.common.constant.DriverStatusConstant;
import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.domain.OrderDetail;
import com.lqzc.common.domain.OrderInfo;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.common.records.DispatchOrderFetchRecords;
import com.lqzc.common.records.DispatchOrderListRecord;
import com.lqzc.common.records.OrderInfoRecords;
import com.lqzc.common.req.OrderDispatchReq;
import com.lqzc.common.req.OrderNewReq;
import com.lqzc.config.RabbitMQConfig;
import com.lqzc.mapper.OrderDetailMapper;
import com.lqzc.service.OrderInfoService;
import com.lqzc.mapper.OrderInfoMapper;
import com.lqzc.utils.OrderNumberGenerator;
import jakarta.annotation.Resource;
import org.redisson.api.RBlockingQueue;
import org.redisson.api.RDelayedQueue;
import org.redisson.api.RLock;
import org.redisson.api.RedissonClient;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.BeanUtils;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.Date;
import java.util.concurrent.TimeUnit;

/**
* @author 11965
* @description 针对表【order_info(订单主表)】的数据库操作Service实现
* @createDate 2025-07-11 09:05:49
*/
@Service
public class OrderInfoServiceImpl extends ServiceImpl<OrderInfoMapper, OrderInfo>
    implements OrderInfoService{
    @Resource
    private OrderInfoMapper orderInfoMapper;
    @Resource
    private OrderDetailMapper orderDetailMapper;
    @Resource
    private StringRedisTemplate stringRedisTemplate;
    @Resource
    private RedissonClient redissonClient;

    @Resource
    private RabbitTemplate rabbitTemplate;

    @Override
    public IPage<DispatchOrderFetchRecords> fetch(IPage<DispatchOrderFetchRecords> page, Integer status) {
        return orderInfoMapper.fetchDispatchOrder4Driver(page,status);
    }

    @Override
    public IPage<DispatchOrderListRecord> getList(IPage<DispatchOrderListRecord> pageNum) {
        return orderInfoMapper.getList(pageNum);
    }

    @Override
    public Boolean robNewOrder(Long id, String orderNo) {
        //判断订单是否存在，通过Redis，减少数据库压力
        if (!stringRedisTemplate.hasKey(RedisConstant.ORDER_WAITING_DRIVER_MARK+orderNo)) {
            //抢单失败
            throw new LianqingException("抢单失败");
        }
        //创建锁 lock:order:ORD123123
        RLock lock = redissonClient.getLock(RedisConstant.LOCK_PREFIX + orderNo);

        try {
            // 尝试获取锁，等待 5 秒，锁持有时间 10 秒
            boolean flag = lock.tryLock(RedisConstant.LOCK_WAITING_TIME, RedisConstant.LOCK_HOLDING_TIME, TimeUnit.SECONDS);
            if (flag) {
                //司机抢单
                //修改order_info表订单状态值1：已经接单 + 司机id + 司机接单时间
                //修改条件：根据订单id
                LambdaQueryWrapper<OrderInfo> wrapper = new LambdaQueryWrapper<>();
                wrapper.eq(OrderInfo::getOrderNo, orderNo);
                OrderInfo orderInfo = orderInfoMapper.selectOne(wrapper);
                //设置派送状态
                orderInfo.setDispatchStatus(DriverStatusConstant.BUSY);
                //设置司机id
                orderInfo.setDriverId(id);
                //调用方法修改
                int rows = orderInfoMapper.updateById(orderInfo);
                if (rows != 1) {
                    //抢单失败
                    throw new LianqingException("抢单失败");
                }
                //删除抢单标识
                stringRedisTemplate.delete(RedisConstant.ORDER_WAITING_DRIVER_MARK+orderNo);
            }
        } catch (Exception e) {
            //抢单失败
            throw new LianqingException(e.getMessage());
        } finally {
            //释放
            if (lock.isLocked()) {
                lock.unlock();
            }
        }
        return true;
    }



    @Override
    public void changeOrderDispatchStatus(String orderNo, int i) {
        int row = orderInfoMapper.changeDispatchStatusByOrderNo(orderNo,i);
        if (row == 0) {
            throw new LianqingException("更改订单信息失败");
        }
        if (i == DispatchConstant.FINISH_DISPATCH){
            // 发送加钱消息
            System.out.println("发送加钱消息: " + orderNo);
            rabbitTemplate.convertAndSend(RabbitMQConfig.ADD_MONEY_EXCHANGE, RabbitMQConfig.ADD_MONEY_ROUTING_KEY, orderNo);
        }
    }
    @Override
    public IPage<OrderInfoRecords> getOrderList(IPage<OrderInfoRecords> page, Integer size, String startStr, String endStr, String customerPhone) {
        return orderInfoMapper.getOrderList(page,startStr,endStr,customerPhone);
    }

    @Override
    public void changeDispatchStatus(Long id, Integer status) {
        OrderInfo orderInfo = orderInfoMapper.selectById(id);
        orderInfo.setDispatchStatus(status);
        orderInfoMapper.updateById(orderInfo);

    }

    @Transactional(rollbackFor = Exception.class)
    @Override
    public void newOrder(OrderNewReq request) {
        //添加orderInfo 总订单
        OrderInfo orderInfo = new OrderInfo();
        BeanUtils.copyProperties(request, orderInfo);
        String orderNo = OrderNumberGenerator.generateOrderNumber();
        orderInfo.setDispatchStatus(DispatchConstant.WAITING_DISPATCH);
        orderInfo.setOrderNo(orderNo);
        orderInfo.setOrderSource(orderInfo.getOrderSource() == null ? 1 : orderInfo.getOrderSource());
        orderInfo.setPayableAmount(orderInfo.getPayableAmount() == null ? orderInfo.getTotalPrice() : orderInfo.getPayableAmount());
        orderInfo.setDiscountAmount(orderInfo.getDiscountAmount() == null ? BigDecimal.ZERO : orderInfo.getDiscountAmount());
        orderInfo.setOrderStatus(orderInfo.getOrderStatus() == null ? 0 : orderInfo.getOrderStatus());
        orderInfo.setPayStatus(orderInfo.getPayStatus() == null ? 0 : orderInfo.getPayStatus());
        orderInfo.setPointsUsed(orderInfo.getPointsUsed() == null ? 0 : orderInfo.getPointsUsed());
        int insert = orderInfoMapper.insert(orderInfo);
        if (insert == 0) {
            throw new RuntimeException("创建总订单失败");
        }
        //添加orderDetail 子订单
        for (OrderNewReq.OrderNewItem item : request.getItems()) {
            OrderDetail orderDetail = new OrderDetail();
            BeanUtils.copyProperties(item, orderDetail);
            //自动回填ID
            orderDetail.setOrderId(orderInfo.getId());
            int insert1 = orderDetailMapper.insert(orderDetail);
            if (insert1 == 0) {
                throw new RuntimeException("创建子订单失败");
            }
        }
    }

    @Transactional(rollbackFor = Exception.class)
    @Override
    public void newOrder(OrderNewReq request,String deliveryAddress) {
        //添加orderInfo 总订单
        OrderInfo orderInfo = new OrderInfo();
        orderInfo.setDeliveryAddress(deliveryAddress);
        BeanUtils.copyProperties(request, orderInfo);
        String orderNo = OrderNumberGenerator.generateOrderNumber();
        orderInfo.setDispatchStatus(DispatchConstant.WAITING_DISPATCH);
        orderInfo.setOrderNo(orderNo);
        orderInfo.setOrderSource(orderInfo.getOrderSource() == null ? 1 : orderInfo.getOrderSource());
        orderInfo.setPayableAmount(orderInfo.getPayableAmount() == null ? orderInfo.getTotalPrice() : orderInfo.getPayableAmount());
        orderInfo.setDiscountAmount(orderInfo.getDiscountAmount() == null ? BigDecimal.ZERO : orderInfo.getDiscountAmount());
        orderInfo.setOrderStatus(orderInfo.getOrderStatus() == null ? 0 : orderInfo.getOrderStatus());
        orderInfo.setPayStatus(orderInfo.getPayStatus() == null ? 0 : orderInfo.getPayStatus());
        orderInfo.setPointsUsed(orderInfo.getPointsUsed() == null ? 0 : orderInfo.getPointsUsed());
        int insert = orderInfoMapper.insert(orderInfo);
        if (insert == 0) {
            throw new RuntimeException("创建总订单失败");
        }
        //添加orderDetail 子订单
        for (OrderNewReq.OrderNewItem item : request.getItems()) {
            OrderDetail orderDetail = new OrderDetail();
            BeanUtils.copyProperties(item, orderDetail);
            //自动回填ID
            orderDetail.setOrderId(orderInfo.getId());
            int insert1 = orderDetailMapper.insert(orderDetail);
            if (insert1 == 0) {
                throw new RuntimeException("创建子订单失败");
            }
        }
    }

    @Transactional(rollbackFor = Exception.class)
    @Override
    public void dispatchOrder(OrderDispatchReq req) {
        System.out.println("req = " + req);
        OrderInfo orderInfo = orderInfoMapper.selectByOrderNo(req.getOrderNo());
        if (orderInfo == null) {
            throw new RuntimeException("获取订单info失败");
        }
        BeanUtils.copyProperties(req, orderInfo);
        orderInfo.setDispatchStatus(DispatchConstant.WAITING_DRIVER);
        orderInfo.setUpdateTime(new Date());
        int updateCount = orderInfoMapper.updateById(orderInfo);
        if (updateCount == 0) {
            throw new RuntimeException("更新订单状态失败，请重试");
        }
        stringRedisTemplate.opsForList().leftPush(RedisConstant.ORDER_WAITING_DRIVER_MARK+orderInfo.getOrderNo(),"待接单订单");
        //过期时间：1分钟
        stringRedisTemplate.expire(RedisConstant.ORDER_WAITING_DRIVER_MARK+orderInfo.getOrderNo(),
                RedisConstant.ORDER_TTL_MARK, TimeUnit.MINUTES);
        this.sendDelayMessage(orderInfo.getId());
    }

    @Override
    public IPage<DispatchOrderFetchRecords> fetch(IPage<DispatchOrderFetchRecords> page, Integer status, String startStr, String endStr, String customerPhone) {
        return orderInfoMapper.fetchDispatchOrder(page,status,startStr,endStr,customerPhone);
    }

    //生成订单之后，发送延迟消息
    private void sendDelayMessage(Long orderId) {
        try {
            System.out.println("准备发送延迟消息，订单No: " + orderId);
            // 获取阻塞队列和延迟队列
            RBlockingQueue<Long> blockingQueue = redissonClient.getBlockingQueue("queue_cancel");
            RDelayedQueue<Long> delayedQueue = redissonClient.getDelayedQueue(blockingQueue);
            System.out.println("准备放入延迟队列的消息内容为: " + orderId);
            // 放入延迟队列，指定延迟时间和单位
            delayedQueue.offer(orderId, RedisConstant.ORDER_TTL_MARK, TimeUnit.MINUTES);
            System.out.println("已成功发送延迟消息到队列 queue_cancel，订单ID: " + orderId);

        } catch (Exception e) {
            e.printStackTrace();
            throw new LianqingException("发送延迟消息失败");
        }
    }

}




