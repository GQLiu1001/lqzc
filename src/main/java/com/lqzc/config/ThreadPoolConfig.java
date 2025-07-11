package com.lqzc.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.concurrent.Executors;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

@Configuration
public class ThreadPoolConfig {


    @Bean
    public ThreadPoolExecutor threadPoolExecutor() {
        int processors = Runtime.getRuntime().availableProcessors();

        return new ThreadPoolExecutor(
                processors * 2,               // corePoolSize (e.g., 16): 保持不变，平时用这些线程处理
                processors * 4,               // maximumPoolSize (e.g., 32): 提供2倍的弹性空间应对峰值
                60,                           // keepAliveTime
                TimeUnit.SECONDS,
                new LinkedBlockingQueue<>(1000),  // workQueue
                Executors.defaultThreadFactory(),
                new ThreadPoolExecutor.AbortPolicy());
    }

}
