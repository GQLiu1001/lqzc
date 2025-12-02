package com.lqzc.common.req;

import lombok.Data;

@Data
public class CustomerRegisterReq {
    /** 手机号 */
    private String phone;
    /** 昵称，未传可由后台默认取后四位 */
    private String nickname;
    /** 登录密码 */
    private String password;
    /** 注册渠道: H5/MiniApp/App */
    private String registerChannel;
}
