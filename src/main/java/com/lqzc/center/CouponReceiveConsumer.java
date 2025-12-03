package com.lqzc.center;

import com.lqzc.common.domain.CustomerCoupon;
import com.lqzc.common.message.CouponReceiveMessage;
import com.lqzc.config.RabbitMQConfig;
import com.lqzc.service.CustomerCouponService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Service;

import java.util.Date;
import java.util.Random;

/**
 * 优惠券领取消息消费者
 * 异步处理发券入库，削峰填谷，保护数据库
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class CouponReceiveConsumer {

    private final CustomerCouponService customerCouponService;

    /**
     * 消费领券消息，异步写入数据库
     */
    @RabbitListener(queues = RabbitMQConfig.COUPON_RECEIVE_QUEUE)
    public void handleCouponReceive(CouponReceiveMessage message) {
        try {
            log.debug("收到领券消息: customerId={}, templateId={}", 
                    message.getCustomerId(), message.getTemplateId());
            
            // 保存领券记录到数据库
            CustomerCoupon coupon = new CustomerCoupon();
            coupon.setCustomerId(message.getCustomerId());
            coupon.setTemplateId(message.getTemplateId());
            coupon.setStatus(0); // 未使用
            coupon.setCode(generateCouponCode());
            coupon.setObtainedChannel("MALL");
            coupon.setExpireTime(message.getExpireTime());
            coupon.setCreateTime(new Date());
            
            customerCouponService.save(coupon);
            
            log.debug("领券入库成功: customerId={}, templateId={}, couponCode={}", 
                    message.getCustomerId(), message.getTemplateId(), coupon.getCode());
                    
        } catch (Exception e) {
            log.error("领券入库失败: customerId={}, templateId={}, error={}", 
                    message.getCustomerId(), message.getTemplateId(), e.getMessage(), e);
            // 消息会被重新投递（根据RabbitMQ配置）
            throw e;
        }
    }

    /**
     * 生成优惠券码
     */
    private String generateCouponCode() {
        return "CPN" + System.currentTimeMillis() + String.format("%04d", new Random().nextInt(10000));
    }
}

