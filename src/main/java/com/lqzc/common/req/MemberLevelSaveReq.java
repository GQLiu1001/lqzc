package com.lqzc.common.req;

import lombok.Data;

@Data
public class MemberLevelSaveReq {
    /** 主键，新增为空 */
    private Long id;
    /** 等级：1=普通 2=银卡 3=金卡 4=黑金 */
    private Integer level;
    /** 等级名称 */
    private String name;
    /** 最低积分 */
    private Integer minPoints;
    /** 最高积分 */
    private Integer maxPoints;
    /** 权益描述 */
    private String benefits;
}
