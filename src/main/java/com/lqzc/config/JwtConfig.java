package com.lqzc.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.time.Duration;

@Data
@Component
@ConfigurationProperties(prefix = "jwt")
public class JwtConfig {

    /**
     * JWT 签名密钥
     */
    private String secret;

    /**
     * 过期时间配置
     */
    private Expiration expiration;

    @Data
    public static class Expiration {
        /**
         * 匿名用户令牌过期时间
         */
        private Duration anonymous;
    }
}