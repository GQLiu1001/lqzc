package com.lqzc.common.resp;

import lombok.Data;

/**
 * 积分流水记录响应
 */
@Data
public class PointsLogItemResp {
    /** 流水ID */
    private Long id;
    /** 客户手机号 */
    private String customerPhone;
    /** 变动积分 */
    private Integer changeAmount;
    /** 变动后余额 */
    private Integer balanceAfter;
    /** 来源：1下单赠送 2退款回退 3支付抵扣 4人工调整 */
    private Integer sourceType;
    /** 关联订单ID */
    private Long orderId;
    /** 备注 */
    private String remark;
    /** 创建时间 */
    private String createTime;
}
