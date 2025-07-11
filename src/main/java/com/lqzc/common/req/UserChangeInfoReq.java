package com.lqzc.common.req;

import lombok.Data;

/**
 * 用户修改信息请求类
 */
@Data
public class UserChangeInfoReq {
    /**
     * 用户名
     */
    private String username;
    
    /**
     * 当前密码
     */
    private String password;
    
    /**
     * 新密码
     */
    private String newPassword;
    
    /**
     * 手机号
     */
    private String phone;
    
    /**
     * 头像URL
     */
    private String avatar;

    private String email;
}
