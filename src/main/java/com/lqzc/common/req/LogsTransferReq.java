package com.lqzc.common.req;

import lombok.Data;

/**
 * 创建调拨记录请求类
 */
@Data
public class LogsTransferReq {
    /**
     * 库存项ID
     */
    private Long itemId;
    
    /**
     * 操作类型（3=调拨）
     */
    private Integer logType;
    
    /**
     * 源仓库编码
     */
    private Integer sourceWarehouse;
    
    /**
     * 目标仓库编码
     */
    private Integer targetWarehouse;
    
    /**
     * 备注
     */
    private String remark;
}
