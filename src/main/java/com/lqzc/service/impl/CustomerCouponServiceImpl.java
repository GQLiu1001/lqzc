package com.lqzc.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.domain.CustomerCoupon;
import com.lqzc.mapper.CustomerCouponMapper;
import com.lqzc.service.CustomerCouponService;
import org.springframework.stereotype.Service;

/**
* @author rabbittank
* @description 针对表【customer_coupon(客户优惠券)】的数据库操作Service实现
* @createDate 2025-07-11 09:05:49
*/
@Service
public class CustomerCouponServiceImpl extends ServiceImpl<CustomerCouponMapper, CustomerCoupon>
    implements CustomerCouponService{

}



