package com.lqzc.common.req;

import lombok.Data;

@Data
public class PointsAdjustReq {
    /** 客户ID */
    private Long customerId;
    /** 变动积分，正加负扣 */
    private Integer changeAmount;
    /** 备注 */
    private String remark;
}
