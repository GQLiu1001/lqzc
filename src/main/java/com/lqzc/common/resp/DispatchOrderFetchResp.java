package com.lqzc.common.resp;

import com.lqzc.common.domain.InventoryItem;
import com.lqzc.common.records.DispatchOrderFetchRecords;
import lombok.Data;
import lombok.Getter;
import lombok.Setter;

import java.math.BigDecimal;
import java.util.List;

/**
 * OrderInfo子字段
 * 获取可用新订单响应类
 */
@Data
@Setter
@Getter
public class DispatchOrderFetchResp {
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
     * 库存记录列表
     */
    private List<DispatchOrderFetchRecords> records;


}
