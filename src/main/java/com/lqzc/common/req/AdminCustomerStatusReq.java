package com.lqzc.common.req;

import lombok.Data;

@Data
public class AdminCustomerStatusReq {
    /** 状态：0停用 1正常 */
    private Integer status;
    /** 原因 */
    private String reason;
}
