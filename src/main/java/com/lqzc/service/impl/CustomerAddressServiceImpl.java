package com.lqzc.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.domain.CustomerAddress;
import com.lqzc.mapper.CustomerAddressMapper;
import com.lqzc.service.CustomerAddressService;
import org.springframework.stereotype.Service;

/**
* @author 11965
* @description 针对表【customer_address(客户收货地址)】的数据库操作Service实现
* @createDate 2025-07-11 09:05:49
*/
@Service
public class CustomerAddressServiceImpl extends ServiceImpl<CustomerAddressMapper, CustomerAddress>
    implements CustomerAddressService{

}



