package com.lqzc.aspect;

import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Pointcut;
import org.springframework.stereotype.Component;

@Aspect
@Component
@Slf4j
public class TimeLogAspect {

    /**
     * 定义切点，匹配所有 controller 包及其子包下的所有类的所有 public 方法
     * execution([修饰符] 返回值类型 [包名.]类名.方法名(参数类型))
     * '..' 代表任意子包或任意参数
     * '*' 代表任意返回值、类名或方法名
     *
     * 根据你的项目结构，controller都在 com.lqzc.XXX.controller 包下，
     * 所以 "execution(public * com.lq.lqzc..controller..*.*(..))" 是一个精准且通用的表达式。
     */
    @Pointcut("execution(public * com.lqzc..controller..*.*(..))")
    public void timeLogPointcut() {
    }

    /**
     * 环绕通知，围绕切点执行
     *
     * @param joinPoint 切点信息
     * @return 方法执行结果
     * @throws Throwable 异常
     */
    @Around("timeLogPointcut()")
    public Object logExecutionTime(ProceedingJoinPoint joinPoint) throws Throwable {
        long startTime = System.currentTimeMillis();

        // 执行目标方法
        Object result = joinPoint.proceed();

        long endTime = System.currentTimeMillis();
        long executionTime = endTime - startTime;

        // 获取类名和方法名
        String className = joinPoint.getTarget().getClass().getName();
        String methodName = joinPoint.getSignature().getName();

        // 记录日志
        // 为了日志整洁，可以增加判断，例如只记录执行时间超过某个阈值（如50ms）的请求
        if (executionTime > 50) {
            log.warn("[Performance Monitor] {} execution was slow: {} ms",  methodName, executionTime);
        } else {
            log.info("[Performance Monitor] {} executed in: {} ms", methodName, executionTime);
        }

        return result;
    }
}
