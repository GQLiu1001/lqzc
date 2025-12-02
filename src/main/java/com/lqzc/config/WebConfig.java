package com.lqzc.config;

import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@RequiredArgsConstructor
@Configuration
public class WebConfig implements WebMvcConfigurer {

    private final MallInterceptor mallInterceptor;
    private final ConsulInterceptor consulInterceptor;
    private final DriverInterceptor driverInterceptor;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        // 注册拦截器并指定拦截路径
        registry.addInterceptor(consulInterceptor)
                .addPathPatterns(
                        "/upload/**",
                        "/inventory/**",
                        "/logs/**",
                        "/manager/**",
                        "/orders/**",
                        "/sales/**",
                        "/selection/**",
                        "/user/**"
                )
                .excludePathPatterns(
                        "/user/login",
                        "/user/register",
                        "/user/reset",
                        "/swagger-ui/**");  // 拦截所有请求

        registry.addInterceptor(mallInterceptor)
                .addPathPatterns(
                        "/mall/**"
                )
                .excludePathPatterns(
                        "/mall/customer/register",
                        "/mall/customer/login",
                        "/mall/customer/forgot-password",
                        "/mall/customer/reset-password",
                        "/mall/items/**",        // 商品列表不需要登录
                        "/mall/selection/**",    // 选品单不需要登录
                        "/mall/ai/**",           // AI助手不需要登录
                        "/mall/coupon/market"    // 领券中心可公开浏览
                );

        registry.addInterceptor(driverInterceptor)
                .addPathPatterns(
                        "/delivery/**",
                        "/driver/**",
                        "/route"
                )
                .excludePathPatterns("/driver/login");  // 拦截所有请求

    }


}
