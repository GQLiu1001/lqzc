package com.lqzc.common.req;

import lombok.Data;

@Data
public class CustomerProfileUpdateReq {
    /** 昵称 */
    private String nickname;
    /** 头像地址 */
    private String avatar;
    /** 邮箱 */
    private String email;
    /** 性别：0未知 1男 2女 */
    private Integer gender;
}
