package com.lqzc.common.resp;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class SalesTrendResp {
  private BigDecimal totalPrice;
  private Long totalAmount;
}
