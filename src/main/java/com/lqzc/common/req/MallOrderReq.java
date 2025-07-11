package com.lqzc.common.req;

import com.lqzc.common.resp.CartItemsResp;
import lombok.Data;

import java.math.BigDecimal;
import java.util.List;

@Data
public class MallOrderReq {
    private String customerPhone;
    private String remark;
    private BigDecimal totalPrice;
    private String deliveryAddress;
    private List<CartItemsResp> items;

}
