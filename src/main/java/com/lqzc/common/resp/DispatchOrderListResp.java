package com.lqzc.common.resp;

import com.lqzc.common.records.DispatchOrderListRecord;
import lombok.Data;
import java.math.BigDecimal;
import java.util.List;

/**
 * 配送订单列表响应类
 * total  List:DispatchOrderListRecord records
 */
@Data
public class DispatchOrderListResp {
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
     * 配送订单记录列表
     */
    private List<DispatchOrderListRecord> records;

}
