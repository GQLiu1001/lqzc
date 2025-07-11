package com.lqzc.aspect;


import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.domain.UserRole;
import com.lqzc.common.exception.LianqingAdminException;
import com.lqzc.mapper.UserRoleMapper;
import jakarta.annotation.Resource;
import jakarta.servlet.http.HttpServletRequest;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestAttributes;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

@Component //注册进SpringBoot
@Aspect //表示这是个切面类
public class LianqingLoginAspect {
    @Resource
    private UserRoleMapper userRoleMapper;
    @Resource
    private StringRedisTemplate stringRedisTemplate;

    //环绕通知，登录判断
    //切入点表达式：指定对哪些规则的方法进行增强
    //*: 表示匹配任何返回类型。 com.lqzc.consul.controller: 目标包。 ..: 表示匹配该包及其所有子包。
    // .: 分隔类名和方法名。*: 表示匹配任何方法名。(..): 表示匹配任意数量和类型的参数。
    @Around("execution(* com.lqzc.controller..*.*(..)) && @annotation(lianqingLogin)")
    public Object login(ProceedingJoinPoint proceedingJoinPoint, LianqingLogin lianqingLogin) throws Throwable {
        //1 获取request对象
        RequestAttributes attributes = RequestContextHolder.getRequestAttributes();
        ServletRequestAttributes sra = (ServletRequestAttributes) attributes;
        HttpServletRequest request = null;
        if (sra != null) {
            request = sra.getRequest();
        }
        //在非 Controller 方法（例如 AOP 切面、Service 层、工具类等）中获取当前 HttpServletRequest 对象的一种非常标准和常用的方式。
        //2 从请求头获取token
        String token = null;
        if (request != null) {
            token = request.getHeader("Authorization").substring(7);
        }
        //3 判断token是否为空，如果为空，返回登录提示
        if (token == null) {
            throw new LianqingAdminException("传入token为空");
        }
        //4 token不为空，查询redis
        String s = stringRedisTemplate.opsForValue().get(RedisConstant.USER_TOKEN + token);
        if (s == null) {
            throw new LianqingAdminException("token无效或已过期，请重新登录");
        }
        //5 查询redis对应用户id,得出RoleId看是否合格
        Long userId = Long.valueOf(s);
        UserRole userRole = userRoleMapper.selectById(userId);
        Long roleId = userRole.getRoleId();
        if (roleId == null || roleId != 1) {
            throw new LianqingAdminException("未授权");
        }
        //6 执行业务方法
        return proceedingJoinPoint.proceed();
    }
}
