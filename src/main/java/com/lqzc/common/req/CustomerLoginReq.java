package com.lqzc.common.req;

import lombok.Data;

@Data
public class CustomerLoginReq {
    /** 手机号 */
    private String phone;
    /** 密码 */
    private String password;
}
