package com.lqzc.common.resp;

import lombok.Data;

@Data
public class CouponRecordResp {
    /** 记录ID */
    private Long id;
    /** 模板ID */
    private Long templateId;
    /** 客户手机号 */
    private String customerPhone;
    /** 状态：0未使用 1已使用 2过期 3作废 */
    private Integer status;
    /** 使用时间 */
    private String useTime;
}
