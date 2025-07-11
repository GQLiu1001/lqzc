package com.lqzc.config.interceptor;


import com.lqzc.utils.UserContextHolder;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.servlet.HandlerInterceptor;

public abstract class AbstractAuthInterceptor implements HandlerInterceptor {
    /**
     * 由子类实现的具体认证逻辑
     * @param token 从请求头中解析出的token
     * @param request HttpServletRequest
     * @return true 如果认证成功，false 如果失败
     */
    protected abstract boolean doAuth(String token, HttpServletRequest request);

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        // 1. 从请求头中获取 Authorization
        String authHeader = request.getHeader("Authorization");

        // 2. 检查 Authorization 是否存在且格式正确
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            // 建议返回一个JSON错误体，而不是空响应
            // response.getWriter().write("{\"error\":\"Missing or invalid Authorization header\"}");
            return false;
        }

        // 3. 提取 token
        String token = authHeader.substring("Bearer ".length()).trim();

        // 4. 调用子类的具体认证逻辑
        if (!doAuth(token, request)) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            return false;
        }

        // 认证成功，放行
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        // 清理 ThreadLocal，防止内存泄漏
        UserContextHolder.clear();
    }
}
