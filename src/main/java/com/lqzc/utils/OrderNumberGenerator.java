package com.lqzc.utils;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Random;

public class OrderNumberGenerator {

    public static String generateOrderNumber() {
        Date date = new Date();
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyyMMddHHmmssSSS");
        String datePart = dateFormat.format(date);
        Random random = new Random();
        // 生成一个0到9999之间的随机整数，然后格式化为4位，不足4位补0
        String randomPart = String.format("%04d", random.nextInt(10000));
        return "ORD" + datePart + randomPart;
    }
    public static String generateSelectionListNumber() {
        Date date = new Date();
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyyMMddHHmmssSSS");
        String datePart = dateFormat.format(date);
        Random random = new Random();
        // 生成一个0到9999之间的随机整数，然后格式化为4位，不足4位补0
        String randomPart = String.format("%04d", random.nextInt(10000));
        return "SEL" + datePart + randomPart;
    }
}
