package com.lqzc.service;

import com.lqzc.common.domain.Driver;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.resp.DriverInfoResp;
import me.chanjar.weixin.common.error.WxErrorException;

import java.math.BigDecimal;
import java.util.List;

/**
* @author rabbittank
* @description 针对表【driver(司机信息表)】的数据库操作Service
* @createDate 2025-07-11 09:05:49
*/
public interface DriverService extends IService<Driver> {

    /**
     * 获取所有司机列表
     *
     * @return 司机列表
     */
    List<Driver> getDriverList();

    /**
     * 审核司机状态
     *
     * @param id     司机ID
     * @param status 审核状态
     */
    void auditDriverWithStatus(Long id, int status);

    /**
     * 重置司机余额
     * <p>
     * 将司机钱包余额归零（通常用于提现后）。
     * </p>
     *
     * @param id 司机ID
     */
    void driverResetMoney(Long id);

    /**
     * 获取司机钱包余额
     *
     * @param id 司机ID
     * @return 钱包余额
     */
    BigDecimal wallet(Long id);

    /**
     * 修改司机状态
     *
     * @param id     司机ID
     * @param status 目标状态
     * @return 修改结果
     */
    Integer changeStatus(Long id, Integer status);

    /**
     * 获取司机审核状态
     *
     * @param id 司机ID
     * @return 审核状态
     */
    Integer auditStatus(Long id);

    /**
     * 司机登录
     * <p>
     * 通过微信授权码和手机号登录。
     * </p>
     *
     * @param code  微信授权码
     * @param phone 手机号
     * @return 司机信息响应
     * @throws WxErrorException 微信接口调用异常
     */
    DriverInfoResp login(String code, String phone) throws WxErrorException;

    /**
     * 更新司机位置
     *
     * @param id        司机ID
     * @param latitude  纬度
     * @param longitude 经度
     */
    void updateLocation(Long id, BigDecimal latitude, BigDecimal longitude);
}
