package com.lqzc.common.resp;

import lombok.Data;

@Data
public class CustomerLoginResp {
    /** 会话 token */
    private String token;
    /** 客户信息 */
    private CustomerInfo customer;

    @Data
    public static class CustomerInfo {
        /** 客户ID */
        private Long id;
        /** 昵称 */
        private String nickname;
        /** 手机号 */
        private String phone;
        /** 头像 */
        private String avatar;
        /** 等级 */
        private Integer level;
        /** 等级名称 */
        private String levelName;
    }
}
