package com.lqzc.common.resp;

import lombok.Data;

/**
 * 销售统计响应类
 */
@Data
public class SalesResp {
    /**
     * 产品型号
     */
    private String model;
    
    /**
     * 销售数量
     */
    private Integer amount;
}
