package com.lqzc.config;

import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
@RequiredArgsConstructor
@Configuration
public class WebConfig implements WebMvcConfigurer {

    private final WebInterceptor webInterceptor;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        // 注册拦截器并指定拦截路径
        registry.addInterceptor(webInterceptor)
//                .addPathPatterns("/**")
                .addPathPatterns("/api/**");
/*                .excludePathPatterns("/user/login","/user/register","/user/reset","/api/user/login", // 添加带api前缀的路径
                        "/api/user/register",
                        "/api/user/reset","/swagger-ui/**");  // 拦截所有请求*/



    }

}
