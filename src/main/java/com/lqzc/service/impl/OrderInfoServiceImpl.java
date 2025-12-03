package com.lqzc.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.constant.DispatchConstant;
import com.lqzc.common.constant.DriverStatusConstant;
import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.domain.CouponTemplate;
import com.lqzc.common.domain.CustomerCoupon;
import com.lqzc.common.domain.CustomerUser;
import com.lqzc.common.domain.OrderDetail;
import com.lqzc.common.domain.OrderInfo;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.common.records.DispatchOrderFetchRecords;
import com.lqzc.common.records.DispatchOrderListRecord;
import com.lqzc.common.records.OrderInfoRecords;
import com.lqzc.common.req.OrderDispatchReq;
import com.lqzc.common.req.OrderNewReq;
import com.lqzc.config.RabbitMQConfig;
import com.lqzc.mapper.CustomerUserMapper;
import com.lqzc.mapper.OrderDetailMapper;
import com.lqzc.common.domain.LoyaltyPointsAccount;
import com.lqzc.common.domain.LoyaltyPointsLog;
import com.lqzc.service.CouponTemplateService;
import com.lqzc.service.CustomerCouponService;
import com.lqzc.service.LoyaltyPointsAccountService;
import com.lqzc.service.LoyaltyPointsLogService;
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
* @author rabbittank
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
    private CustomerUserMapper customerUserMapper;
    @Resource
    private CustomerCouponService customerCouponService;
    @Resource
    private CouponTemplateService couponTemplateService;
    @Resource
    private LoyaltyPointsAccountService pointsAccountService;
    @Resource
    private LoyaltyPointsLogService pointsLogService;
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
            // 司机送达，更新订单状态为"待确认"(3)
            OrderInfo orderInfo = orderInfoMapper.selectOne(
                new LambdaQueryWrapper<OrderInfo>().eq(OrderInfo::getOrderNo, orderNo)
            );
            if (orderInfo != null) {
                orderInfo.setOrderStatus(3); // 待确认
                orderInfo.setReceiveTime(new Date()); // 记录送达时间
                orderInfoMapper.updateById(orderInfo);
            }
            // 发送加钱消息
            System.out.println("发送加钱消息: " + orderNo);
            rabbitTemplate.convertAndSend(RabbitMQConfig.ADD_MONEY_EXCHANGE, RabbitMQConfig.ADD_MONEY_ROUTING_KEY, orderNo);
        }
    }

    /**
     * 确认收货并计算积分
     * 订单状态从3(待确认)变为4(已完成)
     * 积分计算：1元=1积分，去除小数点
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public void confirmReceive(Long orderId, boolean isAdmin) {
        OrderInfo orderInfo = orderInfoMapper.selectById(orderId);
        if (orderInfo == null) {
            throw new LianqingException("订单不存在");
        }
        
        // 验证订单状态必须是"待确认"(3)
        if (orderInfo.getOrderStatus() != 3) {
            throw new LianqingException("订单状态不正确，无法确认收货");
        }
        
        // 更新订单状态为"已完成"(4)
        orderInfo.setOrderStatus(4);
        orderInfo.setUpdateTime(new Date());
        orderInfoMapper.updateById(orderInfo);
        
        // 计算并添加积分（实付金额，1元=1积分，去除小数点）
        if (orderInfo.getCustomerId() != null && orderInfo.getPayableAmount() != null) {
            int earnedPoints = orderInfo.getPayableAmount().intValue(); // 去除小数点
            
            if (earnedPoints > 0) {
                // 获取或创建积分账户
                LoyaltyPointsAccount account = pointsAccountService.getOne(
                    new LambdaQueryWrapper<LoyaltyPointsAccount>()
                        .eq(LoyaltyPointsAccount::getCustomerId, orderInfo.getCustomerId())
                );
                
                if (account == null) {
                    // 创建积分账户
                    account = new LoyaltyPointsAccount();
                    account.setCustomerId(orderInfo.getCustomerId());
                    account.setBalance(0);
                    account.setTotalEarned(0);
                    account.setTotalSpent(0);
                    account.setFrozen(0);
                    account.setCreateTime(new Date());
                    pointsAccountService.save(account);
                }
                
                // 更新积分
                int newBalance = account.getBalance() + earnedPoints;
                int newTotalEarned = account.getTotalEarned() + earnedPoints;
                
                account.setBalance(newBalance);
                account.setTotalEarned(newTotalEarned);
                account.setUpdateTime(new Date());
                pointsAccountService.updateById(account);
                
                // 记录积分日志
                LoyaltyPointsLog log = new LoyaltyPointsLog();
                log.setCustomerId(orderInfo.getCustomerId());
                log.setChangeAmount(earnedPoints); // 正数表示增加
                log.setBalanceAfter(newBalance);
                log.setSourceType(1); // 1=下单赠送
                log.setOrderId(orderInfo.getId());
                log.setRemark(isAdmin ? "订单完成赠送积分(后台确认)" : "订单完成赠送积分(用户确认)");
                log.setCreateTime(new Date());
                pointsLogService.save(log);
            }
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

    /**
     * 更改派送状态并确认支付
     * 当从待派送(0)变为待接单(1)时，表示后台已确认客户支付，同步更新：
     * - dispatch_status: 派送状态
     * - pay_status: 支付状态 -> 1(已支付)
     * - pay_channel: 支付渠道 -> 1(微信)/2(支付宝)
     * - pay_time: 支付时间
     * - order_status: 订单状态 -> 1(已支付/待发货)
     * - coupon_id: 使用的优惠券ID
     * - discount_amount: 优惠金额
     * - payable_amount: 实付金额
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public void changeDispatchStatusWithPayment(Long id, Integer status, String payMethod, Long couponId) {
        OrderInfo orderInfo = orderInfoMapper.selectById(id);
        if (orderInfo == null) {
            throw new LianqingException("订单不存在");
        }
        
        // 更新派送状态
        orderInfo.setDispatchStatus(status);
        
        // 如果是派单操作（状态变为1-待接单），同时确认支付
        if (status == 1 && payMethod != null && !payMethod.isEmpty()) {
            // 更新支付状态为已支付
            orderInfo.setPayStatus(1);
            // 更新支付渠道：wechat=1, alipay=2
            if ("wechat".equals(payMethod)) {
                orderInfo.setPayChannel(1);
            } else if ("alipay".equals(payMethod)) {
                orderInfo.setPayChannel(2);
            }
            // 更新支付时间
            orderInfo.setPayTime(new Date());
            // 更新订单状态为已支付/待发货
            orderInfo.setOrderStatus(1);
            
            // 处理优惠券
            if (couponId != null) {
                CustomerCoupon coupon = customerCouponService.getById(couponId);
                if (coupon != null && coupon.getStatus() == 0) {
                    CouponTemplate template = couponTemplateService.getById(coupon.getTemplateId());
                    if (template != null) {
                        // 计算优惠金额
                        BigDecimal totalPrice = orderInfo.getTotalPrice();
                        BigDecimal discountAmount = calculateCouponDiscount(template, totalPrice);
                        
                        // 更新订单金额
                        orderInfo.setCouponId(couponId);
                        orderInfo.setDiscountAmount(discountAmount);
                        BigDecimal payableAmount = totalPrice.subtract(discountAmount);
                        if (payableAmount.compareTo(BigDecimal.ZERO) < 0) {
                            payableAmount = BigDecimal.ZERO;
                        }
                        orderInfo.setPayableAmount(payableAmount);
                        
                        // 标记优惠券已使用
                        customerCouponService.update(
                                new LambdaUpdateWrapper<CustomerCoupon>()
                                        .eq(CustomerCoupon::getId, couponId)
                                        .set(CustomerCoupon::getStatus, 1)
                                        .set(CustomerCoupon::getUsedOrderId, orderInfo.getId())
                                        .set(CustomerCoupon::getUseTime, new Date())
                        );
                    }
                }
            }
        }
        
        orderInfoMapper.updateById(orderInfo);
    }
    
    /**
     * 计算优惠券优惠金额
     */
    private BigDecimal calculateCouponDiscount(CouponTemplate template, BigDecimal totalPrice) {
        // 检查门槛
        if (template.getThresholdAmount() != null && totalPrice.compareTo(template.getThresholdAmount()) < 0) {
            return BigDecimal.ZERO;
        }
        
        switch (template.getType()) {
            case 1: // 满减券
            case 3: // 现金券
                return template.getDiscountAmount() != null ? template.getDiscountAmount() : BigDecimal.ZERO;
            case 2: // 折扣券（discountRate存储的是小数，如0.9表示9折）
                if (template.getDiscountRate() != null) {
                    // 优惠金额 = 总价 × (1 - 折扣率)
                    // 例如9折：优惠金额 = 69 × (1 - 0.9) = 69 × 0.1 = 6.9
                    BigDecimal discount = totalPrice.multiply(BigDecimal.ONE.subtract(template.getDiscountRate()));
                    // 如果有最大优惠限制
                    if (template.getMaxDiscount() != null && discount.compareTo(template.getMaxDiscount()) > 0) {
                        return template.getMaxDiscount();
                    }
                    return discount;
                }
                return BigDecimal.ZERO;
            default:
                return BigDecimal.ZERO;
        }
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
        
        // 根据customerPhone查询customerId
        if (request.getCustomerPhone() != null && !request.getCustomerPhone().isEmpty()) {
            CustomerUser customer = customerUserMapper.selectOne(
                new LambdaQueryWrapper<CustomerUser>().eq(CustomerUser::getPhone, request.getCustomerPhone())
            );
            if (customer != null) {
                orderInfo.setCustomerId(customer.getId());
            }
        }
        
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
        
        // 根据customerPhone查询customerId
        if (request.getCustomerPhone() != null && !request.getCustomerPhone().isEmpty()) {
            CustomerUser customer = customerUserMapper.selectOne(
                new LambdaQueryWrapper<CustomerUser>().eq(CustomerUser::getPhone, request.getCustomerPhone())
            );
            if (customer != null) {
                orderInfo.setCustomerId(customer.getId());
            }
        }
        
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




