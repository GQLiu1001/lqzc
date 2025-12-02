package com.lqzc.common.req;

import lombok.Data;

@Data
public class ResetPasswordReq {
    /** 手机号 */
    private String phone;
    /** 旧密码 */
    private String oldPassword;
    /** 新密码 */
    private String newPassword;
}
