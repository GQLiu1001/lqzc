package com.lqzc.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.domain.CustomerUser;
import com.lqzc.mapper.CustomerUserMapper;
import com.lqzc.service.CustomerUserService;
import org.springframework.stereotype.Service;

/**
* @author 11965
* @description 针对表【customer_user(前台客户账户)】的数据库操作Service实现
* @createDate 2025-07-11 09:05:49
*/
@Service
public class CustomerUserServiceImpl extends ServiceImpl<CustomerUserMapper, CustomerUser>
    implements CustomerUserService{

}



