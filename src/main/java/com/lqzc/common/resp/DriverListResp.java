package com.lqzc.common.resp;

import com.lqzc.common.domain.Driver;
import lombok.Data;
import java.math.BigDecimal;
import java.util.List;

/**
 * 司机列表响应类
 * total List:Driver records
 */
@Data
public class DriverListResp {
    /**
     * 总记录数
     */
    private Long total;
    
    /**
     * 司机记录列表
     */
    private List<Driver> records;

}
