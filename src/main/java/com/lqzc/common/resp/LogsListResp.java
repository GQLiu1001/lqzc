package com.lqzc.common.resp;

import com.lqzc.common.domain.InventoryLog;
import lombok.Data;
import java.util.List;

/**
 * 出入库及调拨记录列表响应类
 * total current size List:InventoryLog records
 */
@Data
public class LogsListResp {
    /**
     * 总记录数
     */
    private Long total;
    
    /**
     * 当前页
     */
    private Long current;
    
    /**
     * 每页大小
     */
    private Long size;
    
    /**
     * 日志记录列表
     */
    private List<InventoryLog> records;
}
