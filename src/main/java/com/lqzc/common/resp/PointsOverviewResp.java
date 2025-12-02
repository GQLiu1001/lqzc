package com.lqzc.common.resp;

import lombok.Data;

@Data
public class PointsOverviewResp {
    /** 可用积分 */
    private Integer balance;
    /** 冻结积分 */
    private Integer frozen;
    /** 累计获取 */
    private Integer totalEarned;
    /** 累计消耗 */
    private Integer totalSpent;
}
