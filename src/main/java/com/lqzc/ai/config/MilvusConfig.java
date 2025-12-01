package com.lqzc.ai.config;

import io.milvus.client.MilvusServiceClient;
import io.milvus.param.ConnectParam;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class MilvusConfig {

    @Bean
    public MilvusServiceClient milvusClient() {
        ConnectParam connectParam = ConnectParam.newBuilder()
                .withDatabaseName("lqzc_db")
                .withHost("localhost")     // Milvus 容器地址
                .withPort(19530)           // 默认端口
                .build();

        return new MilvusServiceClient(connectParam);
    }
}
