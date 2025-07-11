package com.lqzc.config;

import com.lqzc.common.props.MongoProps;
import com.mongodb.client.MongoClients;
import jakarta.annotation.Resource;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.core.MongoTemplate;

@Configuration
public class MongoConfig {
    @Resource
    private MongoProps mongoProps;

    @Bean
    public MongoTemplate mongoTemplate() {
        return new MongoTemplate(MongoClients.create(mongoProps.setAddress()),mongoProps.getDatabase() );
    }
}
