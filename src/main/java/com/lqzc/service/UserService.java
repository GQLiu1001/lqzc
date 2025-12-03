package com.lqzc.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.User;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.records.UserListRecord;
import com.lqzc.common.req.UserChangeInfoReq;
import com.lqzc.common.resp.UserLoginResp;

/**
* @author rabbittank
* @description 针对表【user(系统用户表)】的数据库操作Service
* @createDate 2025-07-11 09:05:49
*/
public interface UserService extends IService<User> {

    /**
     * 分页查询系统用户列表
     *
     * @param page 分页对象
     * @return 用户分页数据
     */
    IPage<UserListRecord> getUserList(IPage<UserListRecord> page);

    /**
     * 修改用户信息
     *
     * @param request 用户信息变更请求
     */
    void changeUserInfo(UserChangeInfoReq request);

    /**
     * 重置用户密码
     *
     * @param username    用户名
     * @param phone       手机号
     * @param newPassword 新密码
     */
    void reSetPassword(String username, String phone, String newPassword);

    /**
     * 用户注册
     *
     * @param username 用户名
     * @param password 密码
     * @param phone    手机号
     * @return 注册是否成功
     */
    boolean register(String username, String password, String phone);

    /**
     * 用户登录
     *
     * @param username 用户名
     * @param password 密码
     * @return 登录响应（含token和用户信息）
     */
    UserLoginResp login(String username, String password);
}
