package com.lqzc.common.resp;

import com.lqzc.common.records.OrderInfoRecords;
import lombok.Data;

import java.util.List;

/**
 * 订单列表响应类
 * total current size List:OrderInfoRecords records
 */
@Data
public class OrderListResp {
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
     * 订单记录列表
     */
    private List<OrderInfoRecords> records;

}
