package com.lqzc.center;

import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.lqzc.common.domain.Driver;
import com.lqzc.common.domain.OrderInfo;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.config.RabbitMQConfig;
import com.lqzc.mapper.OrderInfoMapper;
import com.lqzc.mapper.DriverMapper;
import jakarta.annotation.Resource;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;

@Service
public class RabbitCenter {
    @Resource
    private OrderInfoMapper orderInfoMapper;
    @Resource
    private DriverMapper driverMapper;

    @Transactional(rollbackFor = Exception.class)
    @RabbitListener(queues = RabbitMQConfig.ADD_MONEY_QUEUE)
    public void addDriverMoney(String orderNo) {
        OrderInfo order = orderInfoMapper.selectByOrderNo(orderNo);
        System.out.println("开始处理rabbitmq: " + order);

        Long driverId = order.getDriverId();
        BigDecimal deliveryFee = order.getDeliveryFee();

        Driver driverInfo = driverMapper.selectById(driverId);
        if (driverInfo == null) {
            System.err.println("找不到司机信息，无法处理司机收益: Driver ID " + driverId);
            // 考虑抛出一个业务异常，让事务回滚，并且RabbitMQ可以重新投递消息
            throw new LianqingException("找不到司机信息: Driver ID " + driverId);
        }

        BigDecimal newMoney = driverInfo.getMoney().add(deliveryFee);
        LambdaUpdateWrapper<Driver> wrapper = new LambdaUpdateWrapper<>();
        wrapper.eq(Driver::getId, driverId);
        wrapper.set(Driver::getMoney, newMoney);

        int rowsAffected = driverMapper.update(null, wrapper);
        if (rowsAffected != 1) {
            // 如果更新失败，抛出异常以触发事务回滚
            throw new LianqingException("更新司机余额失败，受影响行数不为1。司机ID: " + driverId);
        }
        System.out.println("司机(" + driverId + ")完成订单(" + order.getOrderNo() + "), 增加余额: " + deliveryFee);
    }
}
