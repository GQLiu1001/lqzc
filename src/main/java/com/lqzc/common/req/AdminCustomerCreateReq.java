package com.lqzc.common.req;

import lombok.Data;

@Data
public class AdminCustomerCreateReq {
    /** 手机号 */
    private String phone;
    /** 昵称 */
    private String nickname;
    /** 密码，不传可用默认 */
    private String password;
    /** 性别：0未知 1男 2女 */
    private Integer gender;
    /** 备注 */
    private String remark;
}
