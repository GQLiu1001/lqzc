package com.lqzc.config;

import com.lqzc.common.props.RedisProps;
import lombok.RequiredArgsConstructor;
import org.redisson.Redisson;
import org.redisson.api.RedissonClient;
import org.redisson.codec.JsonJacksonCodec;
import org.redisson.config.Config;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@RequiredArgsConstructor
@Configuration
public class RedissonConfig {

    private final RedisProps redisProps;

    @Bean
    public RedissonClient redissonClient() {
        Config config = new Config();
        config.useSingleServer()
                .setAddress(redisProps.getAddress())  // 动态获取
                .setPassword(redisProps.getPassword());
        config.setCodec(new JsonJacksonCodec());
        return Redisson.create(config);
    }

}
