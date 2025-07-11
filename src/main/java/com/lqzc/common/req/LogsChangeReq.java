package com.lqzc.common.req;

import lombok.Data;

/**
 * 出入库或调拨记录修改请求类
 */
@Data
public class LogsChangeReq {
    /**
     * 日志ID
     */
    private Long id;
    
    /**
     * 库存项ID
     */
    private Long itemId;
    
    /**
     * 操作类型（1=入库 2=出库 3=调拨 4=冲正）
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
     * 数量变化
     */
    private Integer amountChange;
    
    /**
     * 操作备注
     */
    private String remark;
}
