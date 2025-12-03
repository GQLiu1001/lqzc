package com.lqzc.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.domain.User;
import com.lqzc.common.domain.UserRole;
import com.lqzc.common.records.UserListRecord;
import com.lqzc.common.req.UserChangeInfoReq;
import com.lqzc.common.resp.UserLoginResp;
import com.lqzc.mapper.UserRoleMapper;
import com.lqzc.service.UserService;
import com.lqzc.mapper.UserMapper;
import com.lqzc.utils.UserContextHolder;
import jakarta.annotation.Resource;
import org.springframework.beans.BeanUtils;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;
import java.util.concurrent.TimeUnit;

/**
* @author rabbittank
* @description 针对表【user(系统用户表)】的数据库操作Service实现
* @createDate 2025-07-11 09:05:49
*/
@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, User>
    implements UserService{

    @Resource
    private UserMapper userMapper;
    @Resource
    private StringRedisTemplate stringRedisTemplate;
    @Resource
    private UserRoleMapper userRoleMapper;
    @Override
    public IPage<UserListRecord> getUserList(IPage<UserListRecord> page) {
        return userMapper.getUserList(page);
    }

    @Override
    public void changeUserInfo(UserChangeInfoReq request) {
        User user = new User();
        BeanUtils.copyProperties(request, user);
        user.setPassword(request.getNewPassword());
        userMapper.updateById(user);
    }

    @Override
    public void reSetPassword(String username, String phone, String newPassword) {
        User user = new User();
        user.setPassword(newPassword);
        user.setUsername(username);
        user.setPhone(phone);
        userMapper.updateById(user);
    }
    @Transactional(rollbackFor = Exception.class)
    @Override
    public boolean register(String username, String password, String phone) {
        User user1 = userMapper.selectOne(new LambdaQueryWrapper<User>().eq(User::getUsername, username));
        if (user1 != null) {
            throw new RuntimeException("注册失败");
        }
        User user2 = userMapper.selectOne(new LambdaQueryWrapper<User>().eq(User::getPhone, phone));
        if (user2 != null) {
            throw new RuntimeException("注册失败");
        }
        User user = new User();
        user.setUsername(username);
        user.setPassword(password);
        user.setPhone(phone);
        userMapper.insert(user);
        UserRole userRole = new UserRole();
        userRole.setUserId(user.getId());
        userRole.setRoleId(2L);
        userRoleMapper.insert(userRole);
        return true;
    }

    @Override
    public UserLoginResp login(String username, String password) {
        LambdaQueryWrapper<User> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(User::getUsername, username);
        queryWrapper.eq(User::getPassword, password);
        User user = userMapper.selectOne(queryWrapper);
        if (user == null) {
            throw new RuntimeException("未知用户");
        }
        String token = UserContextHolder.getUserToken();
        if (!stringRedisTemplate.hasKey(RedisConstant.USER_TOKEN + token)) {
            token = UUID.randomUUID().toString();
            stringRedisTemplate.opsForValue().set(RedisConstant.USER_TOKEN+token, String.valueOf(user.getId()),RedisConstant.USER_TOKEN_AVATIME, TimeUnit.HOURS);
        }
        Long roleId = userMapper.getUserRoleId(user.getId());
        UserLoginResp resp = new UserLoginResp();
        BeanUtils.copyProperties(user, resp);
        resp.setRoleId(roleId);
        resp.setToken(token);
        return resp;
    }

}




