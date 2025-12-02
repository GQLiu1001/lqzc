package com.lqzc.common.resp;

import lombok.Data;

@Data
public class CustomerProfileResp {
    /** 客户ID */
    private Long id;
    /** 昵称 */
    private String nickname;
    /** 手机号 */
    private String phone;
    /** 头像 */
    private String avatar;
    /** 邮箱 */
    private String email;
    /** 性别：0未知 1男 2女 */
    private Integer gender;
    /** 等级 */
    private Integer level;
    /** 可用积分 */
    private Integer pointsBalance;
    /** 优惠券数量 */
    private Integer couponCount;
}
