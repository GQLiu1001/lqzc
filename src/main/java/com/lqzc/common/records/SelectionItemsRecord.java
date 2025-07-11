package com.lqzc.common.records;

import lombok.Data;
import lombok.Getter;

import java.math.BigDecimal;

@Data
public class SelectionItemsRecord {
    private String itemModel;
    private String itemSpecification;
    private BigDecimal itemSellingPrice;
    private Long id;
    private Integer amount;
}
