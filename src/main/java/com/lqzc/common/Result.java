package com.lqzc.common;

import com.lqzc.common.enums.ResultCode;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class Result<T> {
    private Integer code;
    private String message;
    private T data;

    public static <T> Result<T> success(T data) {
        return new Result<>(ResultCode.SUCCESS.getCode(), ResultCode.SUCCESS.getMessage(), data);
    }
    public static <T> Result<T> success() {
        return new Result<>(ResultCode.SUCCESS.getCode(), ResultCode.SUCCESS.getMessage(), null);
    }
    public static <T> Result<T> fail(T data) {
        return new Result<>(ResultCode.FAIL.getCode(), ResultCode.FAIL.getMessage(), data);
    }
    public static <T> Result<T> fail(Integer code,String message,T data) {
        return new Result<>( code,  message, data);
    }
    public static <T> Result<T> fail() {
        return new Result<>(ResultCode.FAIL.getCode(), ResultCode.FAIL.getMessage(), null);
    }

}