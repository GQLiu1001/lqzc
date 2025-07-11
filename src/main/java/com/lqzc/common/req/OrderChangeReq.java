package com.lqzc.common.req;

import lombok.Data;

/**
 * 修改总订单请求类（不包括订单项变更）
 */
@Data
public class OrderChangeReq {
    /**
     * 订单ID
     */
    private Long id;
    
    /**
     * 客户手机号
     */
    private String customerPhone;
    
    /**
     * 订单备注
     */
    private String remark;
}
