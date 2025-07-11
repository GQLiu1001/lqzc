package com.lqzc.config;

import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.domain.UserRole;
import com.lqzc.config.interceptor.AbstractAuthInterceptor;
import com.lqzc.utils.UserContextHolder;
import com.lqzc.mapper.UserRoleMapper;
import jakarta.annotation.Resource;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import java.util.Set;

@Component
public class ConsulInterceptor extends AbstractAuthInterceptor {
    @Resource
    private StringRedisTemplate stringRedisTemplate;
    @Resource
    private UserRoleMapper userRoleMapper;

    @Override
    protected boolean doAuth(String token, HttpServletRequest request) {
        String userId = stringRedisTemplate.opsForValue().get(RedisConstant.USER_TOKEN + token);
        if (userId == null) {
            return false;
        }

        UserRole userRole = userRoleMapper.selectById(userId);
        if (userRole == null || userRole.getRoleId() == null || !this.roleValidator(userRole.getRoleId())) {
            return false;
        }

        // 存入UserContextHolder
        UserContextHolder.setUserId(Long.valueOf(userId));
        UserContextHolder.setUserRoleId(userRole.getRoleId());
        UserContextHolder.setUserToken(token);
        return true;
    }

    // 角色验证逻辑
    private boolean roleValidator(Long roleId) {
        return Set.of(1L, 2L).contains(roleId);
    }
}