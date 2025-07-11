package com.lqzc.utils;

import com.auth0.jwt.JWT;
import com.auth0.jwt.JWTVerifier;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.interfaces.DecodedJWT;
import com.lqzc.config.JwtConfig;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;

import java.util.Date;
import java.util.UUID;

@Component
public class JwtUtils {

    private final JwtConfig jwtConfig;
    private final Algorithm algorithm;

    /**
     * 构造函数，注入配置类，并初始化签名算法
     * @param jwtConfig a
     */
    public JwtUtils(JwtConfig jwtConfig) {
        this.jwtConfig = jwtConfig;
        // 使用 HMAC256 算法，并传入密钥
        this.algorithm = Algorithm.HMAC256(jwtConfig.getSecret());
    }

    /**
     * 为匿名用户生成一个购物车令牌
     * @return 生成的JWT字符串
     */
    public  String generateAnonymousToken() {
        // 生成一个唯一的购物车ID
        String cartId = UUID.randomUUID().toString();

        Date now = new Date();
        // 计算过期时间
        Date expiryDate = new Date(now.getTime() + jwtConfig.getExpiration().getAnonymous().toMillis());

        return JWT.create()
                // >>> Payload（载荷）部分 <<<
                .withClaim("cartId", cartId)      // 自定义声明：购物车ID
                .withClaim("anonymous", true) // 自定义声明：标识为匿名用户
                // >>> 标准声明 <<<
                .withIssuedAt(now)                      // iat: 签发时间
                .withExpiresAt(expiryDate)              // exp: 过期时间
                .withIssuer("lqzc-mall")        // iss: 签发者
                // >>> 签名部分 <<<
                .sign(algorithm);
    }

    /**
     * 验证一个JWT并解码
     * @param token JWT字符串
     * @return 解码后的JWT对象 (DecodedJWT)，如果验证失败则返回null
     */
    public DecodedJWT verifyAndDecodeToken(String token) {
        try {
            // 创建一个验证器，指定算法和签发者
            JWTVerifier verifier = JWT.require(algorithm)
                    .withIssuer("lqzc-mall")
                    .build();
            // 执行验证
            return verifier.verify(token);
        } catch (JWTVerificationException exception){
            // 验证失败（例如：签名错误、令牌过期）
            // 在实际应用中，这里可以打印日志
            System.out.println("JWT verification failed: " + exception.getMessage());
            return null;
        }
    }

    /**
     * 从已解码的JWT中获取 cartId
     * @param decodedJWT a
     * @return 购物车ID
     */
    public String getCartId(DecodedJWT decodedJWT) {
        return decodedJWT.getClaim("cartId").asString();
    }
}