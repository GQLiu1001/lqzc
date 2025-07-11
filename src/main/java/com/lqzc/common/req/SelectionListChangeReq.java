package com.lqzc.common.req;

import lombok.Data;

/**
 * customerPhone deliveryAddress remark
 */
@Data
public class SelectionListChangeReq {

    private String customerPhone;
    private String deliveryAddress;
    private String remark;
}
