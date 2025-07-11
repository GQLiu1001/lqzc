package com.lqzc.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.User;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.records.UserListRecord;
import com.lqzc.common.req.UserChangeInfoReq;
import com.lqzc.common.resp.UserLoginResp;

/**
* @author 11965
* @description 针对表【user(系统用户表)】的数据库操作Service
* @createDate 2025-07-11 09:05:49
*/
public interface UserService extends IService<User> {
    IPage<UserListRecord> getUserList(IPage<UserListRecord> page);

    void changeUserInfo(UserChangeInfoReq request);

    void reSetPassword(String username, String phone, String newPassword);

    boolean register(String username, String password, String phone);

    UserLoginResp login(String username, String password);
}
