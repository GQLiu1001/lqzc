package com.lqzc.common.resp;

import com.lqzc.common.domain.InventoryItem;
import lombok.Data;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

/**
 * 库存列表响应类
 * total current size List:InventoryItem records
 */
@Data
@Setter
@Getter
public class ItemsListResp {
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
    private List<InventoryItem> records;

}
