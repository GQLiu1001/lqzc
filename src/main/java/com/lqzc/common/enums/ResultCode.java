package com.lqzc.common.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;
@AllArgsConstructor
@Getter
public enum ResultCode {

    SUCCESS(200, "成功"),
    FAIL(400, "失败"),
    UNAUTHORIZED(401, "未授权");

    // 获取 code
    private final int code;
    // 获取 message
    private final String message;


}