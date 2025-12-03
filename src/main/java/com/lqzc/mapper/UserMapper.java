package com.lqzc.mapper;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.User;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.lqzc.common.records.UserListRecord;
import org.apache.ibatis.annotations.Select;

/**
* @author rabbittank
* @description 针对表【user(系统用户表)】的数据库操作Mapper
* @createDate 2025-07-11 09:05:49
* @Entity com.lqzc.common.domain.User
*/
public interface UserMapper extends BaseMapper<User> {
    @Select("select u.*,ur.role_id from user u join user_role ur on u.id = ur.user_id")
    IPage<UserListRecord> getUserList(IPage<UserListRecord> page);
    @Select("select role_id from user_role where user_id = #{id}")
    Long getUserRoleId(Long id);

    String getAdminEmail();
}




