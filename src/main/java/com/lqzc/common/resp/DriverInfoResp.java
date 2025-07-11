package com.lqzc.common.resp;

import lombok.Data;

/**
 * 司机信息响应类
 * Driver子字段
 */
@Data
public class DriverInfoResp {
    /**
     * 司机ID
     */
    private Long id;
    
    /**
     * 司机姓名
     */
    private String name;
    
    /**
     * 手机号
     */
    private String phone;
    
    /**
     * 头像URL
     */
    private String avatar;
    
    /**
     * 审核状态(0=未审核,1=已通过,2=已拒绝)
     */
    private Integer auditStatus;
    
    /**
     * 工作状态(0=空闲,1=忙碌,2=离线)
     */
    private Integer workStatus;

    private String token;
}
