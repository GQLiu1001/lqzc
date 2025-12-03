package com.lqzc.common.message;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.Date;

/**
 * 优惠券领取消息体
 * 用于RabbitMQ异步处理发券入库
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class CouponReceiveMessage implements Serializable {
    
    private static final long serialVersionUID = 1L;
    
    /** 用户ID */
    private Long customerId;
    
    /** 优惠券模板ID */
    private Long templateId;
    
    /** 优惠券标题 */
    private String title;
    
    /** 过期时间 */
    private Date expireTime;
    
    /** 消息创建时间 */
    private Long timestamp;
    
    public CouponReceiveMessage(Long customerId, Long templateId, String title, Date expireTime) {
        this.customerId = customerId;
        this.templateId = templateId;
        this.title = title;
        this.expireTime = expireTime;
        this.timestamp = System.currentTimeMillis();
    }
}

