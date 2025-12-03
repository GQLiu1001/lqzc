package com.lqzc.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.lqzc.common.Result;
import com.lqzc.common.domain.CouponTemplate;
import com.lqzc.common.domain.CustomerCoupon;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.common.resp.CouponMarketResp;
import com.lqzc.common.resp.MyCouponResp;
import com.lqzc.service.CouponTemplateService;
import com.lqzc.service.CustomerCouponService;
import com.lqzc.utils.UserContextHolder;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.web.bind.annotation.*;

import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

/**
 * C端优惠券控制器
 * <p>
 * 提供领券中心、抢券、我的优惠券等功能
 * 抢券使用Redis+Lua脚本防止超发
 * </p>
 */
@Tag(name = "C端-优惠券")
@RestController
@RequestMapping("/mall/coupon")
@RequiredArgsConstructor
@Slf4j
public class MallCouponController {

    private final CouponTemplateService couponTemplateService;
    private final CustomerCouponService customerCouponService;
    private final StringRedisTemplate stringRedisTemplate;

    /** Redis key前缀：优惠券库存 */
    private static final String COUPON_STOCK_KEY = "coupon:stock:";
    /** Redis key前缀：用户已领取数量 */
    private static final String COUPON_USER_RECEIVED_KEY = "coupon:user:received:";

    /**
     * 抢券Lua脚本
     * <p>
     * 原子性操作：检查库存、检查用户限领、扣减库存、记录领取
     * </p>
     * KEYS[1]: 库存key
     * KEYS[2]: 用户领取记录key
     * ARGV[1]: 每人限领数量
     * 返回值: 1=成功, 0=库存不足, -1=已达领取上限
     */
    private static final String GRAB_COUPON_LUA_SCRIPT = """
            local stock = tonumber(redis.call('get', KEYS[1]) or 0)
            if stock <= 0 then
                return 0
            end
            local received = tonumber(redis.call('get', KEYS[2]) or 0)
            local limit = tonumber(ARGV[1])
            if received >= limit then
                return -1
            end
            redis.call('decr', KEYS[1])
            redis.call('incr', KEYS[2])
            return 1
            """;

    @Operation(summary = "领券中心列表", description = "获取当前可领取的优惠券模板")
    @GetMapping("/market")
    public Result<List<CouponMarketResp>> market() {
        Long customerId = UserContextHolder.getCustomerId();
        
        // 查询启用且在有效期内的优惠券模板
        Date now = new Date();
        LambdaQueryWrapper<CouponTemplate> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(CouponTemplate::getStatus, 1)
                .le(CouponTemplate::getValidFrom, now)
                .ge(CouponTemplate::getValidTo, now);
        List<CouponTemplate> templates = couponTemplateService.list(queryWrapper);
        
        // 查询用户已领取的优惠券
        Set<Long> receivedTemplateIds = new HashSet<>();
        if (customerId != null) {
            LambdaQueryWrapper<CustomerCoupon> couponQuery = new LambdaQueryWrapper<>();
            couponQuery.eq(CustomerCoupon::getCustomerId, customerId);
            List<CustomerCoupon> myCoupons = customerCouponService.list(couponQuery);
            receivedTemplateIds = myCoupons.stream()
                    .map(CustomerCoupon::getTemplateId)
                    .collect(Collectors.toSet());
        }
        
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        Set<Long> finalReceivedTemplateIds = receivedTemplateIds;
        
        List<CouponMarketResp> respList = templates.stream().map(template -> {
            CouponMarketResp resp = new CouponMarketResp();
            resp.setId(template.getId());
            resp.setTitle(template.getTitle());
            resp.setType(template.getType());
            resp.setThresholdAmount(template.getThresholdAmount());
            resp.setDiscountAmount(template.getDiscountAmount());
            resp.setDiscountRate(template.getDiscountRate());
            resp.setMaxDiscount(template.getMaxDiscount());
            resp.setValidFrom(template.getValidFrom() != null ? sdf.format(template.getValidFrom()) : null);
            resp.setValidTo(template.getValidTo() != null ? sdf.format(template.getValidTo()) : null);
            resp.setIsReceived(finalReceivedTemplateIds.contains(template.getId()));
            return resp;
        }).collect(Collectors.toList());
        
        return Result.success(respList);
    }

    @Operation(summary = "领取优惠券", description = "抢券接口，使用Redis+Lua防止超发")
    @PostMapping("/receive/{templateId}")
    public Result<Void> receive(@Parameter(description = "模板ID") @PathVariable Long templateId) {
        Long customerId = UserContextHolder.getCustomerId();
        
        // 1. 查询优惠券模板
        CouponTemplate template = couponTemplateService.getById(templateId);
        if (template == null) {
            throw new LianqingException("优惠券不存在");
        }
        if (template.getStatus() != 1) {
            throw new LianqingException("优惠券已下架");
        }
        
        Date now = new Date();
        if (template.getValidFrom() != null && now.before(template.getValidFrom())) {
            throw new LianqingException("活动尚未开始");
        }
        if (template.getValidTo() != null && now.after(template.getValidTo())) {
            throw new LianqingException("活动已结束");
        }
        
        // 2. 初始化Redis库存（如果不存在）
        String stockKey = COUPON_STOCK_KEY + templateId;
        String userReceivedKey = COUPON_USER_RECEIVED_KEY + templateId + ":" + customerId;
        
        // 检查并初始化库存到Redis
        initCouponStock(templateId, template);
        
        // 3. 执行Lua脚本抢券
        DefaultRedisScript<Long> script = new DefaultRedisScript<>(GRAB_COUPON_LUA_SCRIPT, Long.class);
        Long result = stringRedisTemplate.execute(
                script,
                Arrays.asList(stockKey, userReceivedKey),
                String.valueOf(template.getPerUserLimit() != null ? template.getPerUserLimit() : 1)
        );
        
        if (result == null || result == 0) {
            throw new LianqingException("优惠券已被抢光");
        }
        if (result == -1) {
            throw new LianqingException("已达领取上限");
        }
        
        // 4. 异步保存领券记录到数据库
        saveCouponRecord(customerId, template);
        
        return Result.success();
    }

    @Operation(summary = "我的优惠券", description = "查询当前用户的优惠券列表")
    @GetMapping("/my-coupons")
    public Result<List<MyCouponResp>> myCoupons(
            @Parameter(description = "状态：0未使用 1已使用 2已过期 3已作废") @RequestParam(required = false) Integer status) {
        Long customerId = UserContextHolder.getCustomerId();
        
        // 查询用户优惠券
        LambdaQueryWrapper<CustomerCoupon> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(CustomerCoupon::getCustomerId, customerId);
        if (status != null) {
            queryWrapper.eq(CustomerCoupon::getStatus, status);
        }
        queryWrapper.orderByDesc(CustomerCoupon::getCreateTime);
        List<CustomerCoupon> coupons = customerCouponService.list(queryWrapper);
        
        // 获取模板信息
        Set<Long> templateIds = coupons.stream()
                .map(CustomerCoupon::getTemplateId)
                .collect(Collectors.toSet());
        
        Map<Long, CouponTemplate> templateMap = new HashMap<>();
        if (!templateIds.isEmpty()) {
            List<CouponTemplate> templates = couponTemplateService.listByIds(templateIds);
            templateMap = templates.stream()
                    .collect(Collectors.toMap(CouponTemplate::getId, t -> t));
        }
        
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'");
        Map<Long, CouponTemplate> finalTemplateMap = templateMap;
        
        List<MyCouponResp> respList = coupons.stream().map(coupon -> {
            MyCouponResp resp = new MyCouponResp();
            resp.setId(coupon.getId());
            resp.setTemplateId(coupon.getTemplateId());
            resp.setCode(coupon.getCode());
            resp.setStatus(coupon.getStatus());
            resp.setExpireTime(coupon.getExpireTime() != null ? sdf.format(coupon.getExpireTime()) : null);
            
            CouponTemplate template = finalTemplateMap.get(coupon.getTemplateId());
            if (template != null) {
                resp.setTitle(template.getTitle());
                resp.setType(template.getType());
                resp.setThresholdAmount(template.getThresholdAmount());
                resp.setDiscountAmount(template.getDiscountAmount());
                resp.setDiscountRate(template.getDiscountRate());
            }
            return resp;
        }).collect(Collectors.toList());
        
        return Result.success(respList);
    }

    /**
     * 初始化优惠券库存到Redis（使用SETNX原子操作，避免重复初始化）
     */
    private void initCouponStock(Long templateId, CouponTemplate template) {
        String stockKey = COUPON_STOCK_KEY + templateId;
        String lockKey = "coupon:init:lock:" + templateId;
        
        // 先快速检查库存key是否存在（大部分请求直接返回）
        String existingStock = stringRedisTemplate.opsForValue().get(stockKey);
        if (existingStock != null) {
            return; // 已初始化，直接返回
        }
        
        // 使用SETNX获取初始化锁，只有一个线程能初始化
        Boolean locked = stringRedisTemplate.opsForValue().setIfAbsent(lockKey, "1", 10, TimeUnit.SECONDS);
        if (Boolean.TRUE.equals(locked)) {
            try {
                // 双重检查
                if (stringRedisTemplate.opsForValue().get(stockKey) != null) {
                    return;
                }
                
                // 计算剩余库存
                long receivedCount = customerCouponService.count(
                        new LambdaQueryWrapper<CustomerCoupon>()
                                .eq(CustomerCoupon::getTemplateId, templateId)
                );
                int remainStock = (template.getTotalIssued() != null ? template.getTotalIssued() : 0) - (int) receivedCount;
                remainStock = Math.max(0, remainStock);
                
                // 设置库存
                stringRedisTemplate.opsForValue().set(stockKey, String.valueOf(remainStock), 7, TimeUnit.DAYS);
                log.info("初始化优惠券库存到Redis: templateId={}, remainStock={}", templateId, remainStock);
            } finally {
                stringRedisTemplate.delete(lockKey);
            }
        }
        // 未获取到锁的线程，等待一下让初始化完成
        else {
            try {
                Thread.sleep(50);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }

    /**
     * 保存领券记录到数据库
     */
    private void saveCouponRecord(Long customerId, CouponTemplate template) {
        CustomerCoupon coupon = new CustomerCoupon();
        coupon.setCustomerId(customerId);
        coupon.setTemplateId(template.getId());
        coupon.setStatus(0); // 未使用
        coupon.setCode(generateCouponCode());
        coupon.setObtainedChannel("MALL");
        coupon.setExpireTime(template.getValidTo());
        coupon.setCreateTime(new Date());
        customerCouponService.save(coupon);
    }

    /**
     * 生成优惠券码
     */
    private String generateCouponCode() {
        return "CPN" + System.currentTimeMillis() + String.format("%04d", new Random().nextInt(10000));
    }
}
