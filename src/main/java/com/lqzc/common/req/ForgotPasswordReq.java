package com.lqzc.common.req;

import lombok.Data;

@Data
public class ForgotPasswordReq {
    /** 手机号 */
    private String phone;
    /** 短信验证码 */
    private String smsCode;
    /** 新密码 */
    private String newPassword;
}
