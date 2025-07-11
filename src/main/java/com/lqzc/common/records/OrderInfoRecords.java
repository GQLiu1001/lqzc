package com.lqzc.common.records;

import lombok.Data;

import java.math.BigDecimal;
import java.util.Date;

/**
 * 订单信息记录类
 * OrderInfo的子字段和其子订单数量subOrderCount
 * @author Rabbittank
 * @since 1.0.0
 */
@Data
public class OrderInfoRecords {
    /**/
    private Long id;
    private String orderNo;
    private String customerPhone;
    private BigDecimal totalPrice;
    private Integer dispatchStatus;
    private String remark;
    private Date createTime;
    private Date updateTime;
    /**
     * 子订单数量
     */
    private Integer subOrderCount;
}
