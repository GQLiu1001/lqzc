//package com.lqzc.config;
//
//import com.auth0.jwt.interfaces.DecodedJWT;
//import com.lqzc.config.interceptor.AbstractAuthInterceptor;
//import com.lqzc.utils.UserContextHolder;
//import com.lqzc.utils.JwtUtils;
//import jakarta.annotation.Resource;
//import jakarta.servlet.http.HttpServletRequest;
//import jakarta.servlet.http.HttpServletResponse;
//import org.springframework.stereotype.Component;
//import org.springframework.web.servlet.HandlerInterceptor;
//
//@Component
//public class MallInterceptor extends AbstractAuthInterceptor {
//    @Resource
//    private JwtUtils jwtUtils;
//
//    @Override
//    protected boolean doAuth(String token, HttpServletRequest request) {
//        DecodedJWT decodedJWT = jwtUtils.verifyAndDecodeToken(token);
//        if (decodedJWT == null) {
//            return false;
//        }
//
//        String cartId = jwtUtils.getCartId(decodedJWT);
//        UserContextHolder.setCartId(cartId);
//        return true;
//    }
//}
