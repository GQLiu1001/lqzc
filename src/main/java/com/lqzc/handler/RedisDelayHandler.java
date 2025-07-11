package com.lqzc.handler;

import com.lqzc.common.constant.DispatchConstant;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.service.OrderInfoService;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.Resource;
import org.redisson.api.RBlockingQueue;
import org.redisson.api.RedissonClient;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RedisDelayHandler {
    @Resource
    private RedissonClient redissonClient;

    @Resource
    private OrderInfoService orderInfoService;

    @PostConstruct
    public void listener() {
        RBlockingQueue<Long> blockingQueue = redissonClient.getBlockingQueue("queue_cancel");
        Thread listenerThread = new Thread(() -> {
            while (true) {try {
                    Long orderId = blockingQueue.take();
                    orderInfoService.changeDispatchStatus(orderId, DispatchConstant.WAITING_DISPATCH);}
            catch (InterruptedException e) {
                    throw new LianqingException("监听线程异常");
                }}},"cancel-order-delay-listener");listenerThread.setDaemon(true);
                listenerThread.start();}}
