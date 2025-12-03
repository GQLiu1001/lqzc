package com.lqzc.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.CustomerUser;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.req.AdminCustomerCreateReq;
import com.lqzc.common.req.AdminCustomerStatusReq;
import com.lqzc.common.req.CustomerLoginReq;
import com.lqzc.common.req.CustomerProfileUpdateReq;
import com.lqzc.common.req.CustomerRegisterReq;
import com.lqzc.common.req.ForgotPasswordReq;
import com.lqzc.common.req.ResetPasswordReq;
import com.lqzc.common.resp.AdminCustomerDetailResp;
import com.lqzc.common.resp.CustomerLoginResp;
import com.lqzc.common.resp.CustomerProfileResp;

/**
 * 客户用户服务接口
 * <p>
 * 提供C端客户管理相关的业务操作，包括：
 * - 客户列表分页查询（支持关键词、等级、状态筛选）
 * - 后台手动创建客户
 * - 客户详情查询（含资产、统计信息）
 * - 客户状态变更（冻结/解冻）
 * </p>
 *
 * @author rabbittank
 * @description 针对表【customer_user(前台客户账户)】的数据库操作Service
 * @createDate 2025-07-11 09:05:49
 */
public interface CustomerUserService extends IService<CustomerUser> {

    /**
     * 分页查询客户列表
     * <p>
     * 根据关键词（手机号或昵称）、会员等级、状态等条件进行分页查询。
     * 查询结果按创建时间倒序排列。
     * </p>
     *
     * @param page    分页对象，包含当前页码和每页条数
     * @param keyword 搜索关键词，可模糊匹配手机号或昵称，可为null
     * @param level   会员等级筛选（1=普通 2=银卡 3=金卡 4=黑金），可为null表示不筛选
     * @param status  状态筛选（1=正常 0=停用），可为null表示不筛选
     * @return 客户分页数据
     */
    IPage<CustomerUser> getCustomerList(IPage<CustomerUser> page, String keyword, Integer level, Integer status);

    /**
     * 后台管理员创建新客户
     * <p>
     * 用于电话订单或线下客户录入场景。
     * 如果未传入密码，默认使用手机号后6位作为初始密码。
     * 创建时会校验手机号是否已存在。
     * </p>
     *
     * @param req 创建客户请求参数，包含手机号、昵称、密码（可选）、性别、备注
     * @throws com.lqzc.common.exception.LianqingAdminException 当手机号已被注册时抛出
     */
    void createCustomer(AdminCustomerCreateReq req);

    /**
     * 获取客户详细信息
     * <p>
     * 聚合查询客户的完整信息，包括：
     * - 基础信息：ID、昵称、手机号、头像等
     * - 资产信息：积分余额、可用优惠券数量
     * - 统计信息：总订单数、总消费金额
     * </p>
     *
     * @param customerId 客户ID
     * @return 客户详情响应对象，包含基础信息、资产、统计数据
     * @throws com.lqzc.common.exception.LianqingAdminException 当客户不存在时抛出
     */
    AdminCustomerDetailResp getCustomerDetail(Long customerId);

    /**
     * 变更客户账号状态
     * <p>
     * 用于冻结或解冻客户账号。
     * 冻结后客户将无法登录和下单。
     * 状态变更会记录操作原因。
     * </p>
     *
     * @param customerId 客户ID
     * @param req        状态变更请求，包含目标状态（0=停用 1=正常）和变更原因
     * @throws com.lqzc.common.exception.LianqingAdminException 当客户不存在时抛出
     */
    void changeCustomerStatus(Long customerId, AdminCustomerStatusReq req);

    /**
     * 确保客户存在，如不存在则自动创建
     * <p>
     * 用于创建订单时，如果输入的手机号不存在于系统中，
     * 自动创建一个新客户账户。
     * </p>
     *
     * @param phone 客户手机号
     * @return 客户ID
     */
    Long ensureCustomerExists(String phone);

    // ==================== C端用户接口 ====================

    /**
     * C端用户注册
     *
     * @param req 注册请求
     * @throws com.lqzc.common.exception.LianqingAdminException 当手机号已注册时抛出
     */
    void register(CustomerRegisterReq req);

    /**
     * C端用户登录
     *
     * @param req 登录请求
     * @return 登录响应（含token和用户信息）
     * @throws com.lqzc.common.exception.LianqingAdminException 当手机号不存在或密码错误时抛出
     */
    CustomerLoginResp login(CustomerLoginReq req);

    /**
     * C端用户登出
     *
     * @param token 用户token
     */
    void logout(String token);

    /**
     * 获取用户个人信息
     *
     * @param customerId 客户ID
     * @return 个人信息
     */
    CustomerProfileResp getProfile(Long customerId);

    /**
     * 修改个人信息
     *
     * @param customerId 客户ID
     * @param req        修改请求
     */
    void updateProfile(Long customerId, CustomerProfileUpdateReq req);

    /**
     * 重置密码（需要旧密码）
     *
     * @param req 重置密码请求
     * @throws com.lqzc.common.exception.LianqingAdminException 当旧密码错误时抛出
     */
    void resetPassword(ResetPasswordReq req);

    /**
     * 忘记密码（短信验证）
     * <p>
     * 简化实现：不校验短信验证码
     * </p>
     *
     * @param req 忘记密码请求
     */
    void forgotPassword(ForgotPasswordReq req);

    /**
     * 根据token获取客户ID
     *
     * @param token 用户token
     * @return 客户ID，如token无效返回null
     */
    Long getCustomerIdByToken(String token);
}
