package com.lqzc.service;

import com.lqzc.common.domain.Driver;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.resp.DriverInfoResp;
import me.chanjar.weixin.common.error.WxErrorException;

import java.math.BigDecimal;
import java.util.List;

/**
* @author 11965
* @description 针对表【driver(司机信息表)】的数据库操作Service
* @createDate 2025-07-11 09:05:49
*/
public interface DriverService extends IService<Driver> {
    List<Driver> getDriverList();

    void auditDriverWithStatus(Long id, int status);

    void driverResetMoney(Long id);

    BigDecimal wallet(Long id);

    Integer changeStatus(Long id, Integer status);

    Integer auditStatus(Long id);

    DriverInfoResp login(String code, String phone) throws WxErrorException;

    void updateLocation(Long id, BigDecimal latitude, BigDecimal longitude);
}
