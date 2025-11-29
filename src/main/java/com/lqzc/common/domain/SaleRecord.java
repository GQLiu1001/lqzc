package com.lqzc.common.domain;

import lombok.Data;
import lombok.Getter;
import lombok.Setter;
//import org.springframework.data.mongodb.core.index.CompoundIndex;

@Setter
@Getter
@Data
//@CompoundIndex(name = "syncDate_model_unique_idx", def = "{'syncDate': 1, 'model': 1}", unique = true)
public class SaleRecord {
    private String model;
    private Integer amount;
    private String syncDate;

}
