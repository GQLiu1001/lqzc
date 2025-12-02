package com.lqzc.common.resp;

import java.math.BigDecimal;
import lombok.Data;

@Data
public class AdminCustomerDetailResp {
    /** 基础信息 */
    private BaseInfo baseInfo;
    /** 资产信息 */
    private Assets assets;
    /** 统计 */
    private Stats stats;

    @Data
    public static class BaseInfo {
        /** 客户ID */
        private Long id;
        /** 昵称 */
        private String nickname;
        /** 手机号 */
        private String phone;
        /** 头像 */
        private String avatar;
    }

    @Data
    public static class Assets {
        /** 积分余额 */
        private Integer pointsBalance;
        /** 优惠券数量 */
        private Integer couponCount;
    }

    @Data
    public static class Stats {
        /** 总订单数 */
        private Integer totalOrders;
        /** 总消费额 */
        private BigDecimal totalSpent;
    }
}
