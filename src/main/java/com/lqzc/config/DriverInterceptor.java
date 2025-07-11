package com.lqzc.config;

import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.domain.Driver;
import com.lqzc.config.interceptor.AbstractAuthInterceptor;
import com.lqzc.utils.UserContextHolder;
import com.lqzc.mapper.DriverMapper;
import jakarta.annotation.Resource;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class DriverInterceptor extends AbstractAuthInterceptor {
    @Resource
    private StringRedisTemplate stringRedisTemplate;
    @Resource
    private DriverMapper driverMapper;

    @Override
    protected boolean doAuth(String token, HttpServletRequest request) {
        String driverId = stringRedisTemplate.opsForValue().get(RedisConstant.DRIVER_TOKEN + token);
        if (driverId == null) {
            return false;
        }

        Driver driver = driverMapper.selectById(driverId);
        if (driver == null) {
            return false;
        }

        // 存入UserContextHolder
        UserContextHolder.setDriverId(driver.getId());
        UserContextHolder.setUserToken(token);
        return true;
    }
}
