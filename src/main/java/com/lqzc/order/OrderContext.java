package com.lqzc.order;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.lqzc.common.domain.LoyaltyPointsAccount;
import com.lqzc.common.domain.LoyaltyPointsLog;
import com.lqzc.common.domain.OrderInfo;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.config.RabbitMQConfig;
import com.lqzc.mapper.OrderInfoMapper;
import com.lqzc.service.LoyaltyPointsAccountService;
import com.lqzc.service.LoyaltyPointsLogService;
import org.springframework.amqp.rabbit.core.RabbitTemplate;

import java.util.Date;

/**
 * @author rabbittank
 * @description 订单状态处理上下文，封装订单实体及积分、MQ 等依赖
 * @createDate 2025-12-10 00:00:00
 */
public class OrderContext {
    private final OrderInfo orderInfo;
    private final OrderInfoMapper orderInfoMapper;
    private final LoyaltyPointsAccountService pointsAccountService;
    private final LoyaltyPointsLogService pointsLogService;
    private final RabbitTemplate rabbitTemplate;
    private boolean adminOperation;

    public OrderContext(OrderInfo orderInfo,
                        OrderInfoMapper orderInfoMapper,
                        LoyaltyPointsAccountService pointsAccountService,
                        LoyaltyPointsLogService pointsLogService,
                        RabbitTemplate rabbitTemplate) {
        this.orderInfo = orderInfo;
        this.orderInfoMapper = orderInfoMapper;
        this.pointsAccountService = pointsAccountService;
        this.pointsLogService = pointsLogService;
        this.rabbitTemplate = rabbitTemplate;
    }

    public OrderInfo getOrderInfo() {
        return orderInfo;
    }

    public void setAdminOperation(boolean adminOperation) {
        this.adminOperation = adminOperation;
    }

    public boolean isAdminOperation() {
        return adminOperation;
    }

    public Date now() {
        return new Date();
    }

    /**
     * 持久化订单修改并刷新更新时间。
     */
    public void saveOrder() {
        orderInfo.setUpdateTime(now());
        int rows = orderInfoMapper.updateById(orderInfo);
        if (rows == 0) {
            throw new LianqingException("更改订单信息失败");
        }
    }

    /**
     * 发送派送完成后的加钱 MQ 消息。
     */
    public void sendAddMoneyMessage() {
        rabbitTemplate.convertAndSend(RabbitMQConfig.ADD_MONEY_EXCHANGE,
                RabbitMQConfig.ADD_MONEY_ROUTING_KEY,
                orderInfo.getOrderNo());
    }

    /**
     * 订单完成后赠送积分。
     *
     * @return 实际赠送的积分
     */
    public int grantCompletionPoints() {
        if (orderInfo.getCustomerId() == null || orderInfo.getPayableAmount() == null) {
            return 0;
        }
        int earnedPoints = orderInfo.getPayableAmount().intValue();
        if (earnedPoints <= 0) {
            return 0;
        }

        LoyaltyPointsAccount account = pointsAccountService.getOne(
                new LambdaQueryWrapper<LoyaltyPointsAccount>()
                        .eq(LoyaltyPointsAccount::getCustomerId, orderInfo.getCustomerId())
        );

        if (account == null) {
            account = new LoyaltyPointsAccount();
            account.setCustomerId(orderInfo.getCustomerId());
            account.setBalance(0);
            account.setTotalEarned(0);
            account.setTotalSpent(0);
            account.setFrozen(0);
            account.setCreateTime(now());
            pointsAccountService.save(account);
        }

        int currentBalance = account.getBalance() == null ? 0 : account.getBalance();
        int currentTotalEarned = account.getTotalEarned() == null ? 0 : account.getTotalEarned();

        int newBalance = currentBalance + earnedPoints;
        int newTotalEarned = currentTotalEarned + earnedPoints;

        account.setBalance(newBalance);
        account.setTotalEarned(newTotalEarned);
        account.setUpdateTime(now());
        pointsAccountService.updateById(account);

        LoyaltyPointsLog log = new LoyaltyPointsLog();
        log.setCustomerId(orderInfo.getCustomerId());
        log.setChangeAmount(earnedPoints);
        log.setBalanceAfter(newBalance);
        log.setSourceType(1);
        log.setOrderId(orderInfo.getId());
        log.setRemark(adminOperation ? "订单完成赠送积分(后台确认)" : "订单完成赠送积分(用户确认)");
        log.setCreateTime(now());
        pointsLogService.save(log);

        return earnedPoints;
    }
}
