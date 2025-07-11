package com.lqzc.common.resp;

import lombok.Data;

/**
 * 用户登录响应类
 * User roleKey
 */
@Data
public class UserLoginResp {
    /**
     * 用户ID
     */
    private Long id;
    
    /**
     * 用户名
     */
    private String username;
    
    /**
     * 头像URL
     */
    private String avatar;
    
    /**
     * 手机号
     */
    private String phone;
    
    /**
     * 角色标识
     */
    private Long roleId;

    private String token;

    private String email;
}
