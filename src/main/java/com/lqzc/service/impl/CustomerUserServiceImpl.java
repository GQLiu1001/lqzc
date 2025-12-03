package com.lqzc.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.domain.CustomerCoupon;
import com.lqzc.common.domain.CustomerUser;
import com.lqzc.common.domain.LoyaltyPointsAccount;
import com.lqzc.common.exception.LianqingAdminException;
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
import com.lqzc.mapper.CustomerCouponMapper;
import com.lqzc.mapper.CustomerUserMapper;
import com.lqzc.mapper.LoyaltyPointsAccountMapper;
import com.lqzc.service.CustomerUserService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

/**
 * 客户用户服务实现类
 * <p>
 * 实现C端客户管理的核心业务逻辑，包括客户的增删改查、
 * 状态管理、详情聚合查询等功能。
 * </p>
 *
 * @author rabbittank
 * @description 针对表【customer_user(前台客户账户)】的数据库操作Service实现
 * @createDate 2025-07-11 09:05:49
 */
@Service
@RequiredArgsConstructor
public class CustomerUserServiceImpl extends ServiceImpl<CustomerUserMapper, CustomerUser>
        implements CustomerUserService {

    private final CustomerUserMapper customerUserMapper;
    private final LoyaltyPointsAccountMapper loyaltyPointsAccountMapper;
    private final CustomerCouponMapper customerCouponMapper;
    private final StringRedisTemplate stringRedisTemplate;

    /** C端用户token前缀 */
    private static final String CUSTOMER_TOKEN_PREFIX = "customer:token:";
    /** Token有效期（7天） */
    private static final long TOKEN_EXPIRE_DAYS = 7;

    /**
     * 分页查询客户列表
     * <p>
     * 使用MyBatis-Plus的LambdaQueryWrapper构建动态查询条件：
     * - keyword：模糊匹配手机号或昵称（OR条件）
     * - level：精确匹配会员等级
     * - status：精确匹配账号状态
     * 结果按创建时间倒序排列
     * </p>
     *
     * @param page    分页对象，包含当前页码和每页条数
     * @param keyword 搜索关键词，可模糊匹配手机号或昵称，可为null
     * @param level   会员等级筛选（1=普通 2=银卡 3=金卡 4=黑金），可为null表示不筛选
     * @param status  状态筛选（1=正常 0=停用），可为null表示不筛选
     * @return 客户分页数据，包含total总数和records记录列表
     */
    @Override
    public IPage<CustomerUser> getCustomerList(IPage<CustomerUser> page, String keyword, Integer level, Integer status) {
        // 构建动态查询条件
        LambdaQueryWrapper<CustomerUser> queryWrapper = new LambdaQueryWrapper<>();

        // 关键词模糊搜索：匹配手机号或昵称
        if (StringUtils.hasText(keyword)) {
            queryWrapper.and(wrapper -> wrapper
                    .like(CustomerUser::getPhone, keyword)
                    .or()
                    .like(CustomerUser::getNickname, keyword)
            );
        }

        // 会员等级精确筛选
        if (level != null) {
            queryWrapper.eq(CustomerUser::getLevel, level);
        }

        // 账号状态精确筛选
        if (status != null) {
            queryWrapper.eq(CustomerUser::getStatus, status);
        }

        // 按创建时间倒序排列，最新注册的客户排在前面
        queryWrapper.orderByDesc(CustomerUser::getCreateTime);

        return customerUserMapper.selectPage(page, queryWrapper);
    }

    /**
     * 后台管理员创建新客户
     * <p>
     * 业务流程：
     * 1. 校验手机号是否已被注册
     * 2. 构建客户实体，设置默认值
     * 3. 保存客户信息到数据库
     * 4. 为新客户创建积分账户
     * </p>
     *
     * @param req 创建客户请求参数
     * @throws LianqingAdminException 当手机号已被注册时抛出
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public void createCustomer(AdminCustomerCreateReq req) {
        // 1. 校验手机号唯一性
        Long existCount = customerUserMapper.selectCount(
                new LambdaQueryWrapper<CustomerUser>()
                        .eq(CustomerUser::getPhone, req.getPhone())
        );
        if (existCount > 0) {
            throw new LianqingAdminException("该手机号已被注册");
        }

        // 2. 构建客户实体
        CustomerUser customer = new CustomerUser();
        customer.setPhone(req.getPhone());
        customer.setNickname(req.getNickname());
        customer.setAvatar("https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=200");
        // 性别：默认为0（未知）
        customer.setGender(req.getGender() != null ? req.getGender() : 0);
        // 会员等级：默认为1（普通会员）
        customer.setLevel(1);
        // 账号状态：默认为1（正常）
        customer.setStatus(1);
        // 注册渠道：标记为后台创建
        customer.setRegisterChannel("ADMIN");
        customer.setCreateTime(new Date());
        customer.setUpdateTime(new Date());

        // 3. 保存客户信息
        customerUserMapper.insert(customer);

        // 4. 为新客户创建积分账户
        LoyaltyPointsAccount pointsAccount = new LoyaltyPointsAccount();
        pointsAccount.setCustomerId(customer.getId());
        pointsAccount.setBalance(0);
        pointsAccount.setTotalEarned(0);
        pointsAccount.setTotalSpent(0);
        pointsAccount.setFrozen(0);
        pointsAccount.setCreateTime(new Date());
        pointsAccount.setUpdateTime(new Date());
        loyaltyPointsAccountMapper.insert(pointsAccount);
    }

    /**
     * 获取客户详细信息
     * <p>
     * 聚合多表数据，返回客户完整信息视图：
     * 1. 查询客户基础信息
     * 2. 查询积分账户余额
     * 3. 统计可用优惠券数量
     * 4. 统计订单数量和消费总额
     * </p>
     *
     * @param customerId 客户ID
     * @return 客户详情响应对象
     * @throws LianqingAdminException 当客户不存在时抛出
     */
    @Override
    public AdminCustomerDetailResp getCustomerDetail(Long customerId) {
        // 1. 查询客户基础信息
        CustomerUser customer = customerUserMapper.selectById(customerId);
        if (customer == null) {
            throw new LianqingAdminException("客户不存在");
        }

        AdminCustomerDetailResp resp = new AdminCustomerDetailResp();

        // 2. 设置基础信息
        AdminCustomerDetailResp.BaseInfo baseInfo = new AdminCustomerDetailResp.BaseInfo();
        baseInfo.setId(customer.getId());
        baseInfo.setNickname(customer.getNickname());
        baseInfo.setPhone(customer.getPhone());
        baseInfo.setAvatar(customer.getAvatar());
        baseInfo.setLevel(customer.getLevel());
        baseInfo.setLevelName(getLevelName(customer.getLevel()));
        baseInfo.setStatus(customer.getStatus());
        baseInfo.setRegisterChannel(customer.getRegisterChannel());
        if (customer.getCreateTime() != null) {
            baseInfo.setCreateTime(new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(customer.getCreateTime()));
        }
        resp.setBaseInfo(baseInfo);

        // 3. 查询资产信息
        AdminCustomerDetailResp.Assets assets = new AdminCustomerDetailResp.Assets();

        // 3.1 查询积分余额
        LoyaltyPointsAccount pointsAccount = loyaltyPointsAccountMapper.selectOne(
                new LambdaQueryWrapper<LoyaltyPointsAccount>()
                        .eq(LoyaltyPointsAccount::getCustomerId, customerId)
        );
        assets.setPointsBalance(pointsAccount != null ? pointsAccount.getBalance() : 0);

        // 3.2 统计可用优惠券数量（状态为0=未使用）
        Long couponCount = customerCouponMapper.selectCount(
                new LambdaQueryWrapper<CustomerCoupon>()
                        .eq(CustomerCoupon::getCustomerId, customerId)
                        .eq(CustomerCoupon::getStatus, 0)
        );
        assets.setCouponCount(couponCount.intValue());
        resp.setAssets(assets);

        // 4. 统计订单信息（使用Mapper的自定义SQL查询）
        AdminCustomerDetailResp.Stats stats = new AdminCustomerDetailResp.Stats();
        Map<String, Object> orderStats = customerUserMapper.selectOrderStats(customerId);
        if (orderStats != null) {
            // 总订单数
            Object totalOrdersObj = orderStats.get("totalOrders");
            stats.setTotalOrders(totalOrdersObj != null ? ((Number) totalOrdersObj).intValue() : 0);
            // 总消费额
            Object totalSpentObj = orderStats.get("totalSpent");
            stats.setTotalSpent(totalSpentObj != null ? new BigDecimal(totalSpentObj.toString()) : BigDecimal.ZERO);
        } else {
            stats.setTotalOrders(0);
            stats.setTotalSpent(BigDecimal.ZERO);
        }
        resp.setStats(stats);

        return resp;
    }

    /**
     * 变更客户账号状态
     * <p>
     * 更新客户的状态字段，用于冻结或解冻账号。
     * 变更原因会记录到日志中（预留扩展）。
     * </p>
     *
     * @param customerId 客户ID
     * @param req        状态变更请求
     * @throws LianqingAdminException 当客户不存在时抛出
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public void changeCustomerStatus(Long customerId, AdminCustomerStatusReq req) {
        // 1. 校验客户是否存在
        CustomerUser customer = customerUserMapper.selectById(customerId);
        if (customer == null) {
            throw new LianqingAdminException("客户不存在");
        }

        // 2. 更新客户状态
        CustomerUser updateCustomer = new CustomerUser();
        updateCustomer.setId(customerId);
        updateCustomer.setStatus(req.getStatus());
        updateCustomer.setUpdateTime(new Date());
        customerUserMapper.updateById(updateCustomer);

        // TODO: 可扩展记录状态变更日志，包含操作原因 req.getReason()
    }

    /**
     * 根据等级编号获取等级名称
     */
    private String getLevelName(Integer level) {
        if (level == null) return "未知";
        switch (level) {
            case 1: return "普通会员";
            case 2: return "银卡会员";
            case 3: return "金卡会员";
            case 4: return "钻石会员";
            default: return "未知";
        }
    }

    /**
     * 确保客户存在，如不存在则自动创建
     * <p>
     * 用于创建订单等场景，当手机号不存在时自动创建客户账户。
     * 新创建的客户使用手机号后4位作为默认昵称。
     * </p>
     *
     * @param phone 客户手机号
     * @return 客户ID
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long ensureCustomerExists(String phone) {
        // 1. 检查客户是否已存在
        CustomerUser existingCustomer = customerUserMapper.selectOne(
                new LambdaQueryWrapper<CustomerUser>()
                        .eq(CustomerUser::getPhone, phone)
        );
        if (existingCustomer != null) {
            return existingCustomer.getId();
        }

        // 2. 客户不存在，自动创建
        CustomerUser customer = new CustomerUser();
        customer.setPhone(phone);
        // 默认昵称：手机号后4位 + 用户
        customer.setNickname("用户" + phone.substring(phone.length() - 4));
        customer.setAvatar("https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=200");
        customer.setGender(0); // 未知
        customer.setLevel(1);  // 普通会员
        customer.setStatus(1); // 正常
        customer.setRegisterChannel("ORDER"); // 标记为订单自动创建
        customer.setCreateTime(new Date());
        customer.setUpdateTime(new Date());
        customerUserMapper.insert(customer);

        // 3. 为新客户创建积分账户
        LoyaltyPointsAccount pointsAccount = new LoyaltyPointsAccount();
        pointsAccount.setCustomerId(customer.getId());
        pointsAccount.setBalance(0);
        pointsAccount.setTotalEarned(0);
        pointsAccount.setTotalSpent(0);
        pointsAccount.setFrozen(0);
        pointsAccount.setCreateTime(new Date());
        pointsAccount.setUpdateTime(new Date());
        loyaltyPointsAccountMapper.insert(pointsAccount);

        return customer.getId();
    }

    // ==================== C端用户接口实现 ====================

    /**
     * C端用户注册
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public void register(CustomerRegisterReq req) {
        // 1. 校验手机号唯一性
        Long existCount = customerUserMapper.selectCount(
                new LambdaQueryWrapper<CustomerUser>()
                        .eq(CustomerUser::getPhone, req.getPhone())
        );
        if (existCount > 0) {
            throw new LianqingAdminException("该手机号已被注册");
        }

        // 2. 构建客户实体
        CustomerUser customer = new CustomerUser();
        customer.setPhone(req.getPhone());
        // 昵称：如果未传，则默认使用手机号后4位
        customer.setNickname(StringUtils.hasText(req.getNickname())
                ? req.getNickname()
                : "用户" + req.getPhone().substring(req.getPhone().length() - 4));
        customer.setPassword(req.getPassword());
        customer.setAvatar("https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=200");
        customer.setGender(0);
        customer.setLevel(1);
        customer.setStatus(1);
        customer.setRegisterChannel(StringUtils.hasText(req.getRegisterChannel())
                ? req.getRegisterChannel()
                : "H5");
        customer.setCreateTime(new Date());
        customer.setUpdateTime(new Date());
        customerUserMapper.insert(customer);

        // 3. 创建积分账户
        LoyaltyPointsAccount pointsAccount = new LoyaltyPointsAccount();
        pointsAccount.setCustomerId(customer.getId());
        pointsAccount.setBalance(0);
        pointsAccount.setTotalEarned(0);
        pointsAccount.setTotalSpent(0);
        pointsAccount.setFrozen(0);
        pointsAccount.setCreateTime(new Date());
        pointsAccount.setUpdateTime(new Date());
        loyaltyPointsAccountMapper.insert(pointsAccount);
    }

    /**
     * C端用户登录
     */
    @Override
    public CustomerLoginResp login(CustomerLoginReq req) {
        // 1. 查询用户
        CustomerUser customer = customerUserMapper.selectOne(
                new LambdaQueryWrapper<CustomerUser>()
                        .eq(CustomerUser::getPhone, req.getPhone())
        );
        if (customer == null) {
            throw new LianqingAdminException("手机号未注册");
        }

        // 2. 校验密码
        if (customer.getPassword() == null || !customer.getPassword().equals(req.getPassword())) {
            throw new LianqingAdminException("密码错误");
        }

        // 3. 校验状态
        if (customer.getStatus() != null && customer.getStatus() == 0) {
            throw new LianqingAdminException("账号已被停用");
        }

        // 4. 生成token并存入Redis
        String token = UUID.randomUUID().toString().replace("-", "");
        stringRedisTemplate.opsForValue().set(
                CUSTOMER_TOKEN_PREFIX + token,
                customer.getId().toString(),
                TOKEN_EXPIRE_DAYS,
                TimeUnit.DAYS
        );

        // 5. 更新最近登录时间
        CustomerUser updateCustomer = new CustomerUser();
        updateCustomer.setId(customer.getId());
        updateCustomer.setLastLoginTime(new Date());
        customerUserMapper.updateById(updateCustomer);

        // 6. 构建响应
        CustomerLoginResp resp = new CustomerLoginResp();
        resp.setToken(token);

        CustomerLoginResp.CustomerInfo customerInfo = new CustomerLoginResp.CustomerInfo();
        customerInfo.setId(customer.getId());
        customerInfo.setNickname(customer.getNickname());
        customerInfo.setPhone(customer.getPhone());
        customerInfo.setAvatar(customer.getAvatar());
        customerInfo.setLevel(customer.getLevel());
        customerInfo.setLevelName(getLevelName(customer.getLevel()));
        resp.setCustomer(customerInfo);

        return resp;
    }

    /**
     * C端用户登出
     */
    @Override
    public void logout(String token) {
        if (StringUtils.hasText(token)) {
            stringRedisTemplate.delete(CUSTOMER_TOKEN_PREFIX + token);
        }
    }

    /**
     * 获取用户个人信息
     */
    @Override
    public CustomerProfileResp getProfile(Long customerId) {
        CustomerUser customer = customerUserMapper.selectById(customerId);
        if (customer == null) {
            throw new LianqingAdminException("用户不存在");
        }

        CustomerProfileResp resp = new CustomerProfileResp();
        resp.setId(customer.getId());
        resp.setNickname(customer.getNickname());
        resp.setPhone(customer.getPhone());
        resp.setAvatar(customer.getAvatar());
        resp.setEmail(customer.getEmail());
        resp.setGender(customer.getGender());
        resp.setLevel(customer.getLevel());

        // 查询积分余额
        LoyaltyPointsAccount pointsAccount = loyaltyPointsAccountMapper.selectOne(
                new LambdaQueryWrapper<LoyaltyPointsAccount>()
                        .eq(LoyaltyPointsAccount::getCustomerId, customerId)
        );
        resp.setPointsBalance(pointsAccount != null ? pointsAccount.getBalance() : 0);

        // 统计可用优惠券数量
        Long couponCount = customerCouponMapper.selectCount(
                new LambdaQueryWrapper<CustomerCoupon>()
                        .eq(CustomerCoupon::getCustomerId, customerId)
                        .eq(CustomerCoupon::getStatus, 0)
        );
        resp.setCouponCount(couponCount.intValue());

        return resp;
    }

    /**
     * 修改个人信息
     */
    @Override
    public void updateProfile(Long customerId, CustomerProfileUpdateReq req) {
        CustomerUser updateCustomer = new CustomerUser();
        updateCustomer.setId(customerId);
        if (StringUtils.hasText(req.getNickname())) {
            updateCustomer.setNickname(req.getNickname());
        }
        if (StringUtils.hasText(req.getAvatar())) {
            updateCustomer.setAvatar(req.getAvatar());
        }
        if (StringUtils.hasText(req.getEmail())) {
            updateCustomer.setEmail(req.getEmail());
        }
        if (req.getGender() != null) {
            updateCustomer.setGender(req.getGender());
        }
        updateCustomer.setUpdateTime(new Date());
        customerUserMapper.updateById(updateCustomer);
    }

    /**
     * 重置密码（需要旧密码）
     */
    @Override
    public void resetPassword(ResetPasswordReq req) {
        // 1. 查询用户
        CustomerUser customer = customerUserMapper.selectOne(
                new LambdaQueryWrapper<CustomerUser>()
                        .eq(CustomerUser::getPhone, req.getPhone())
        );
        if (customer == null) {
            throw new LianqingAdminException("手机号未注册");
        }

        // 2. 校验旧密码
        if (customer.getPassword() == null || !customer.getPassword().equals(req.getOldPassword())) {
            throw new LianqingAdminException("旧密码错误");
        }

        // 3. 更新新密码
        CustomerUser updateCustomer = new CustomerUser();
        updateCustomer.setId(customer.getId());
        updateCustomer.setPassword(req.getNewPassword());
        updateCustomer.setUpdateTime(new Date());
        customerUserMapper.updateById(updateCustomer);
    }

    /**
     * 忘记密码（短信验证）
     * 简化实现：不校验短信验证码，直接重置
     */
    @Override
    public void forgotPassword(ForgotPasswordReq req) {
        // 1. 查询用户
        CustomerUser customer = customerUserMapper.selectOne(
                new LambdaQueryWrapper<CustomerUser>()
                        .eq(CustomerUser::getPhone, req.getPhone())
        );
        if (customer == null) {
            throw new LianqingAdminException("手机号未注册");
        }

        // 2. 简化实现：不校验短信验证码，直接更新密码
        // 实际生产环境应该校验 req.getSmsCode()
        CustomerUser updateCustomer = new CustomerUser();
        updateCustomer.setId(customer.getId());
        updateCustomer.setPassword(req.getNewPassword());
        updateCustomer.setUpdateTime(new Date());
        customerUserMapper.updateById(updateCustomer);
    }

    /**
     * 根据token获取客户ID
     */
    @Override
    public Long getCustomerIdByToken(String token) {
        if (!StringUtils.hasText(token)) {
            return null;
        }
        String customerId = stringRedisTemplate.opsForValue().get(CUSTOMER_TOKEN_PREFIX + token);
        return customerId != null ? Long.parseLong(customerId) : null;
    }
}
