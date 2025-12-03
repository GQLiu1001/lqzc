package com.lqzc.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.domain.OrderPayment;
import com.lqzc.mapper.OrderPaymentMapper;
import com.lqzc.service.OrderPaymentService;
import org.springframework.stereotype.Service;

/**
* @author rabbittank
* @description 针对表【order_payment(订单支付记录)】的数据库操作Service实现
* @createDate 2025-07-11 09:05:49
*/
@Service
public class OrderPaymentServiceImpl extends ServiceImpl<OrderPaymentMapper, OrderPayment>
    implements OrderPaymentService{

}



