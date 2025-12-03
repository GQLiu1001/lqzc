package com.lqzc.service.impl;

import cn.binarywang.wx.miniapp.api.WxMaService;
import cn.binarywang.wx.miniapp.bean.WxMaJscode2SessionResult;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.constant.DriverAuditStatusConstant;
import com.lqzc.common.constant.DriverStatusConstant;
import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.domain.Driver;
import com.lqzc.common.resp.DriverInfoResp;
import com.lqzc.service.DriverService;
import com.lqzc.mapper.DriverMapper;
import jakarta.annotation.Resource;
import me.chanjar.weixin.common.error.WxErrorException;
import org.springframework.beans.BeanUtils;
import org.springframework.data.geo.Point;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.Date;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

/**
 * @author rabbittank
 * @description 针对表【driver(司机信息表)】的数据库操作Service实现
 * @createDate 2025-07-11 09:05:49
 */
@Service
public class DriverServiceImpl extends ServiceImpl<DriverMapper, Driver>
        implements DriverService {
    @Resource
    private DriverMapper driverMapper;

    @Resource
    private StringRedisTemplate stringRedisTemplate;

    @Resource
    private WxMaService wxMaService;

    @Override
    public DriverInfoResp login(String code, String phone) throws WxErrorException {
        String openid;
        //1.获取code值 使用微信工具包对象(WxMaService) 获取微信唯一标识 openid
        WxMaJscode2SessionResult sessionInfo = wxMaService.getUserService().getSessionInfo(code);
        openid = sessionInfo.getOpenid();
        //2.根据openid判断是否第一次登录 是-》添加信息到用户表 返回用户id值 plus登录日志
        QueryWrapper<Driver> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("openid", openid);
        Driver driverInfo = driverMapper.selectOne(queryWrapper);
        if (driverInfo == null) {
            driverInfo = new Driver();
            driverInfo.setOpenid(openid);
            driverInfo.setPhone(phone);
            driverInfo.setAvatar("");
            driverInfo.setName("newDriver" + phone);
            driverInfo.setAuditStatus(DriverAuditStatusConstant.TO_BE_AUDIT);
            driverInfo.setWorkStatus(DriverStatusConstant.OFFLINE);
            driverInfo.setMoney(BigDecimal.valueOf(0));
            driverInfo.setCreateTime(new Date());
            driverInfo.setUpdateTime(new Date());
            driverMapper.insert(driverInfo);
        }
        String token = null;
        if (!stringRedisTemplate.hasKey(RedisConstant.DRIVER_TOKEN + driverInfo.getId())) {
            token = UUID.randomUUID().toString();
            stringRedisTemplate.opsForValue().set(RedisConstant.DRIVER_TOKEN + token, String.valueOf(driverInfo.getId()), RedisConstant.USER_TOKEN_AVATIME, TimeUnit.HOURS);
        }
        DriverInfoResp loginInfoResp = new DriverInfoResp();
        loginInfoResp.setToken(token);
        BeanUtils.copyProperties(driverInfo, loginInfoResp);
        return loginInfoResp;
    }

    @Override
    public BigDecimal wallet(Long id) {
        Driver driver = driverMapper.selectById(id);
        return driver.getMoney();
    }

    @Override
    public Integer changeStatus(Long id, Integer status) {
        Driver driver = driverMapper.selectById(id);
        driver.setWorkStatus(status);
        return driverMapper.updateById(driver);
    }

    @Override
    public Integer auditStatus(Long id) {
        Driver driver = driverMapper.selectById(id);
        return driver.getAuditStatus();
    }

    @Override
    public void updateLocation(Long id, BigDecimal latitude, BigDecimal longitude) {
        if (id == null || latitude == null || longitude == null) {
            throw new IllegalArgumentException("id, latitude 或 longitude 不能为空");
        }
        // 将 BigDecimal 转换为 double，Redis GEO 需要 double 类型
        double lat = latitude.doubleValue();
        double lon = longitude.doubleValue();
        // 校验经纬度范围
        if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
            throw new IllegalArgumentException("经纬度超出有效范围（纬度: -90~90，经度: -180~180）");
        }
        // 使用 Redis GEO 存储位置
        stringRedisTemplate.opsForGeo().add(RedisConstant.DRIVER_LOCATION, new Point(lon, lat), String.valueOf(id));
    }

    @Override
    public List<Driver> getDriverList() {
        return driverMapper.getDriverList();
    }

    @Override
    public void auditDriverWithStatus(Long id, int status) {
        Driver driver = driverMapper.selectById(id);
        driver.setAuditStatus(status);
        driverMapper.updateById(driver);
    }

    @Override
    public void driverResetMoney(Long id) {
        Driver driver = driverMapper.selectById(id);
        driver.setMoney(BigDecimal.valueOf(0));
        driverMapper.updateById(driver);
    }
}




