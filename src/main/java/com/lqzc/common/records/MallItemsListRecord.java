package com.lqzc.common.records;

import com.baomidou.mybatisplus.annotation.Version;
import lombok.Data;

import java.math.BigDecimal;
import java.util.Date;

@Data
public class MallItemsListRecord {

    private String model;
    private String manufacturer;
    private String specification;
    private Integer surface;
    private Integer category;
    private Integer totalAmount;

    private String picture;
    private BigDecimal sellingPrice;
}
