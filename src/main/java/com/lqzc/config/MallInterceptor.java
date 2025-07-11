package com.lqzc.config;

import com.auth0.jwt.interfaces.DecodedJWT;
import com.lqzc.utils.UserContextHolder;
import com.lqzc.utils.JwtUtils;
import jakarta.annotation.Resource;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class MallInterceptor implements HandlerInterceptor {
    @Resource
    private JwtUtils jwtUtils;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        // 1. 从请求头获取Token
        String authHeader = request.getHeader("Authorization");
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            // 没传Token，返回401
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            return false;
        }
        String token = authHeader.substring(7);

        // 2. 验证并解码Token
        DecodedJWT decodedJWT = jwtUtils.verifyAndDecodeToken(token);
        if (decodedJWT == null) {
            // Token无效，返回401
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            return false;
        }

        // 3. 从Token中提取信息，并传递给后续的Controller
        String cartId = jwtUtils.getCartId(decodedJWT);
        // 通常的做法是把 cartId 存入 ThreadLocal 或直接作为 request attribute，方便Controller获取
        UserContextHolder.setCartId(cartId);
        return true; // 放行请求
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) throws Exception {
        // 请求处理完毕后，必须清理ThreadLocal，防止内存泄漏
        UserContextHolder.clear();
    }
}
