package com.lqzc.config;

import com.lqzc.service.CustomerUserService;
import com.lqzc.utils.UserContextHolder;
import jakarta.annotation.Resource;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * Mall端拦截器
 * <p>
 * 验证C端用户登录token（Redis UUID token）
 * 支持从X-Customer-Token header获取token
 * </p>
 */
@Component
public class MallInterceptor implements HandlerInterceptor {

    @Resource
    private CustomerUserService customerUserService;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        // 从X-Customer-Token获取登录用户token
        String token = request.getHeader("X-Customer-Token");
        
        if (token == null || token.isEmpty()) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write("{\"code\":401,\"message\":\"请先登录\"}");
            return false;
        }
        
        // 验证token并获取customerId
        Long customerId = customerUserService.getCustomerIdByToken(token);
        if (customerId == null) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write("{\"code\":401,\"message\":\"登录已过期，请重新登录\"}");
            return false;
        }
        
        // 设置customerId到ThreadLocal
        UserContextHolder.setCustomerId(customerId);
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        // 清理ThreadLocal
        UserContextHolder.clear();
    }
}
