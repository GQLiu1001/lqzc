package com.lqzc.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.domain.UserRole;
import com.lqzc.service.UserRoleService;
import com.lqzc.mapper.UserRoleMapper;
import org.springframework.stereotype.Service;

/**
* @author 11965
* @description 针对表【user_role(用户角色关联表)】的数据库操作Service实现
* @createDate 2025-07-11 09:05:49
*/
@Service
public class UserRoleServiceImpl extends ServiceImpl<UserRoleMapper, UserRole>
    implements UserRoleService{

}




