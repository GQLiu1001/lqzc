package com.lqzc.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.domain.Role;
import com.lqzc.service.RoleService;
import com.lqzc.mapper.RoleMapper;
import org.springframework.stereotype.Service;

/**
* @author 11965
* @description 针对表【role(角色表)】的数据库操作Service实现
* @createDate 2025-07-11 09:05:49
*/
@Service
public class RoleServiceImpl extends ServiceImpl<RoleMapper, Role>
    implements RoleService{

}




