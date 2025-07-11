package com.lqzc.common.resp;

import lombok.Data;

/**
 * 根据型号自动回填ID和数量响应类
 */
@Data
public class IetmsFetchResp {
    /**
     * 库存ID
     */
    private Long id;
    
    /**
     * 库存总数量
     */
    private Integer totalAmount;
}
