package com.lqzc.common.req;

import lombok.Data;

import java.math.BigDecimal;

/**
 * itemModel itemSellingPrice amount
 */
@Data
public class SelectionItemAddReq {
    private String itemModel;
    private BigDecimal itemSellingPrice;
    private Integer amount;
}
