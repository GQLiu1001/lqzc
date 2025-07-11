package com.lqzc.common.constant;

public class RedisConstant {


    public static final String USER_TOKEN = "login:user:";
    public static final Integer USER_TOKEN_AVATIME = 24;
    public static final String DRIVER_TOKEN = "login:delivery:";
    public static final Integer DRIVER_TOKEN_AVATIME = 24;

    public static final String DRIVER_LOCATION = "driver:locations";

    public static final String LOCK_PREFIX = "order:lock:";
    public static final Integer LOCK_WAITING_TIME = 5;
    public static final Integer LOCK_HOLDING_TIME = 10;

    public static final String ORDER_WAITING_DRIVER_MARK = "order:waiting:driver:";
    public static final Integer ORDER_TTL_MARK = 1;


    public static final String HOT_SALES = "hot:sales:";
    public static final String HOT_SALES_ARCHIVE = "hot:sales:archive:";

    public static final Integer BATCH_SIZE = 50;

    public static final String CART_ID = "cart:id:";
}
