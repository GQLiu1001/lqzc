package com.lqzc.common.resp;

import lombok.Data;

@Data
public class MyCouponResp {
    /** 券ID */
    private Long id;
    /** 模板ID */
    private Long templateId;
    /** 标题 */
    private String title;
    /** 券码 */
    private String code;
    /** 状态：0未使用 1已使用 2已过期 3已作废 */
    private Integer status;
    /** 过期时间 */
    private String expireTime;
}
