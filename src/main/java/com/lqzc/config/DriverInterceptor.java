package com.lqzc.config;

import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.domain.Driver;
import com.lqzc.utils.UserContextHolder;
import com.lqzc.mapper.DriverMapper;
import jakarta.annotation.Resource;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class DriverInterceptor implements HandlerInterceptor {
    @Resource
    private StringRedisTemplate stringRedisTemplate;
    @Resource
    private DriverMapper driverMapper;
    // 在请求处理之前执行
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        // 从请求头中获取 Authorization
        String authHeader = request.getHeader("Authorization");

        // 检查 Authorization 是否存在且格式正确
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            // 提取 token
            String token = authHeader.substring("Bearer ".length()).trim();
            String driverId = stringRedisTemplate.opsForValue().get(RedisConstant.DRIVER_TOKEN + token);
            if (driverId != null ) {
                Driver driver = driverMapper.selectById(driverId);
                if (driver.getId() != null) {
                    //id存在 存入UserContextHolder
                    UserContextHolder.setDriverId(Long.valueOf(driverId));
                    UserContextHolder.setUserToken(token);
                    return true;
                }
            } else {
                // token 无效，返回 401 未授权
                response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                return false;
            }
        }

        // Authorization 头缺失或格式错误，返回 401 未授权
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        System.out.println("头缺失");
        return false;
    }

    // 在请求处理完成后执行
    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                Object handler, Exception ex) {
        // 清理 ThreadLocal，防止内存泄漏
        UserContextHolder.clear();
    }


}
