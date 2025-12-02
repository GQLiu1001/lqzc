package com.lqzc.common;

import java.util.List;
import lombok.Data;

@Data
public class PageResp<T> {
    /** 总条数 */
    private Long total;
    /** 数据列表 */
    private List<T> records;
}
