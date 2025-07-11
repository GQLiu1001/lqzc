package com.lqzc.common.resp;

import lombok.Data;
import lombok.Setter;

import java.math.BigDecimal;
@Setter
@Data
public class CartItemsResp {
    private String model;
    private Integer amount;
}
