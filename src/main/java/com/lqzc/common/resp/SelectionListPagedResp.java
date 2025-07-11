package com.lqzc.common.resp;

import com.lqzc.common.domain.InventoryItem;
import com.lqzc.common.domain.SelectionList;
import lombok.Data;

import java.util.List;
@Data
public class SelectionListPagedResp {
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
    private List<SelectionList> records;
}
