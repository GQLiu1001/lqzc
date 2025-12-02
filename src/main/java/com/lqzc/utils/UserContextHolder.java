package com.lqzc.utils;

public class UserContextHolder {
    //用户ID
    private static final ThreadLocal<Long> USER_ID = new ThreadLocal<>();
    public static void setUserId(Long userId) {
        USER_ID.set(userId);
    }
    public static Long getUserId() {
        return USER_ID.get();
    }

    //用户ID
    private static final ThreadLocal<String> USER_TOKEN = new ThreadLocal<>();
    public static void setUserToken(String userToken) {
        USER_TOKEN.set(userToken);
    }
    public static String getUserToken() {
        return USER_TOKEN.get();
    }


    // 角色 ID
    private static final ThreadLocal<Long> ROLE_ID = new ThreadLocal<>();
    public static void setUserRoleId(Long roleId) {
        ROLE_ID.set(roleId);
    }
    public static Long getUserRoleId() {
        return ROLE_ID.get();
    }

    //司机ID
    private static final ThreadLocal<Long> DRIVER_ID = new ThreadLocal<>();
    public static void setDriverId(Long driverId) {
        DRIVER_ID.set(driverId);
    }
    public static Long getDriverId() {
        return DRIVER_ID.get();
    }

    //匿名ID（购物车）
    private static final ThreadLocal<String> CART_ID = new ThreadLocal<>();
    public static void setCartId(String cartId) {
        CART_ID.set(cartId);
    }
    public static String getCartId() {
        return CART_ID.get();
    }

    //C端客户ID
    private static final ThreadLocal<Long> CUSTOMER_ID = new ThreadLocal<>();
    public static void setCustomerId(Long customerId) {
        CUSTOMER_ID.set(customerId);
    }
    public static Long getCustomerId() {
        return CUSTOMER_ID.get();
    }

    // 清理 ThreadLocal，防止内存泄露
    public static void clear() {
        USER_ID.remove();
        ROLE_ID.remove();
        DRIVER_ID.remove();
        CART_ID.remove();
        USER_TOKEN.remove();
        CUSTOMER_ID.remove();
    }

}
