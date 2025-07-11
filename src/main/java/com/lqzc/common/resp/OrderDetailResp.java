package com.lqzc.common.resp;

import com.lqzc.common.domain.OrderDetail;
import lombok.Data;
import java.math.BigDecimal;
import java.util.Date;
import java.util.List;

/**
 * 订单详情响应类
 * OrderInfo 以及相应的 子订单List:OrderDetail subOrder
 */
@Data
public class OrderDetailResp {
    /**
     * 订单ID
     */
    private Long id;
    
    /**
     * 订单编号
     */
    private String orderNo;
    
    /**
     * 客户手机号
     */
    private String customerPhone;
    
    /**
     * 订单总金额
     */
    private BigDecimal totalPrice;
    
    /**
     * 创建时间
     */
    private Date createTime;
    
    /**
     * 更新时间
     */
    private Date updateTime;
    
    /**
     * 子订单列表
     */
    private List<OrderDetail> subOrder;
    
    /**
     * 订单备注
     */
    private String remark;

}
