package com.lqzc.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lqzc.common.Result;
import com.lqzc.common.domain.CouponTemplate;
import com.lqzc.common.domain.CustomerCoupon;
import com.lqzc.common.domain.CustomerUser;
import com.lqzc.common.req.CouponTemplateCreateReq;
import com.lqzc.common.resp.CouponRecordResp;
import com.lqzc.common.resp.CouponTemplateListResp;
import com.lqzc.common.resp.CustomerAvailableCouponResp;
import com.lqzc.common.PageResp;
import com.lqzc.service.CouponTemplateService;
import com.lqzc.service.CustomerCouponService;
import com.lqzc.service.CustomerUserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

/**
 * 后台优惠券管理控制器
 * <p>
 * 提供优惠券模板管理的REST API接口，包括：
 * - 创建优惠券模板
 * - 查询模板列表（含统计数据）
 * - 模板上下架
 * - 查询发放记录
 * </p>
 * <p>
 * 说明：Controller层只负责处理分页参数等与业务无关的代码，
 * 具体业务逻辑由Service层实现。
 * </p>
 *
 * @author rabbittank
 */
@Tag(name = "后台-优惠券管理")
@RestController
@RequestMapping("/admin/coupon")
@RequiredArgsConstructor
public class AdminCouponController {

    private final CouponTemplateService couponTemplateService;
    private final CustomerCouponService customerCouponService;
    private final CustomerUserService customerUserService;

    /**
     * 创建优惠券模板
     * <p>
     * 创建新的优惠券活动，支持满减、折扣、现金券三种类型。
     * </p>
     *
     * @param req 创建请求参数
     * @return 操作结果
     */
    @Operation(summary = "创建优惠券模板")
    @PostMapping("/create")
    public Result<Void> create(@RequestBody CouponTemplateCreateReq req) {
        couponTemplateService.createTemplate(req);
        return Result.success();
    }

    /**
     * 分页查询优惠券模板列表
     * <p>
     * 返回模板信息及统计数据（已领取数量、已核销数量）。
     * 支持按状态和标题筛选。
     * </p>
     *
     * @param current 当前页码，默认1
     * @param size    每页条数，默认10
     * @param status  状态筛选（1启用 0停用），可选
     * @param title   标题模糊搜索，可选
     * @return 模板分页数据
     */
    @Operation(summary = "优惠券模板列表")
    @GetMapping("/list")
    public Result<PageResp<CouponTemplateListResp>> list(
            @Parameter(description = "当前页码") @RequestParam(defaultValue = "1") Integer current,
            @Parameter(description = "每页条数") @RequestParam(defaultValue = "10") Integer size,
            @Parameter(description = "状态筛选（1启用 0停用）") @RequestParam(required = false) Integer status,
            @Parameter(description = "标题模糊搜索") @RequestParam(required = false) String title) {

        // 构建分页对象
        IPage<CouponTemplateListResp> page = new Page<>(current, size);

        // 调用Service层进行业务查询
        IPage<CouponTemplateListResp> result = couponTemplateService.getTemplateList(page, status, title);

        // 封装分页响应
        PageResp<CouponTemplateListResp> resp = new PageResp<>();
        resp.setTotal(result.getTotal());
        resp.setRecords(result.getRecords());

        return Result.success(resp);
    }

    /**
     * 变更优惠券模板状态（上下架）
     * <p>
     * 下架后用户无法继续领取该券，但已领取的券仍可使用。
     * </p>
     *
     * @param id     模板ID
     * @param status 目标状态（0=停用 1=启用）
     * @return 操作结果
     */
    @Operation(summary = "优惠券上下架")
    @PutMapping("/status/{id}")
    public Result<Void> changeStatus(
            @Parameter(description = "模板ID") @PathVariable Long id,
            @Parameter(description = "状态（0停用 1启用）") @RequestParam Integer status) {
        couponTemplateService.changeTemplateStatus(id, status);
        return Result.success();
    }

    /**
     * 分页查询优惠券发放记录
     * <p>
     * 查询客户领取优惠券的详细记录。
     * 支持按模板ID、客户手机号、使用状态筛选。
     * </p>
     *
     * @param current       当前页码，默认1
     * @param size          每页条数，默认10
     * @param templateId    模板ID筛选，可选
     * @param customerPhone 客户手机号筛选，可选
     * @param status        使用状态筛选（0未使用 1已使用 2过期 3作废），可选
     * @return 发放记录分页数据
     */
    @Operation(summary = "优惠券发放记录")
    @GetMapping("/record/list")
    public Result<PageResp<CouponRecordResp>> records(
            @Parameter(description = "当前页码") @RequestParam(defaultValue = "1") Integer current,
            @Parameter(description = "每页条数") @RequestParam(defaultValue = "10") Integer size,
            @Parameter(description = "模板ID筛选") @RequestParam(required = false) Long templateId,
            @Parameter(description = "客户手机号筛选") @RequestParam(required = false) String customerPhone,
            @Parameter(description = "使用状态（0未使用 1已使用 2过期 3作废）") @RequestParam(required = false) Integer status) {

        // 构建分页对象
        IPage<CouponRecordResp> page = new Page<>(current, size);

        // 调用Service层进行业务查询
        IPage<CouponRecordResp> result = couponTemplateService.getCouponRecordList(page, templateId, customerPhone, status);

        // 封装分页响应
        PageResp<CouponRecordResp> resp = new PageResp<>();
        resp.setTotal(result.getTotal());
        resp.setRecords(result.getRecords());

        return Result.success(resp);
    }

    /**
     * 获取用户可用优惠券列表（后台派单时使用）
     * <p>
     * 根据客户手机号查询其可用的优惠券，用于后台派单时选择使用哪张优惠券。
     * 可传入订单金额用于计算优惠金额。
     * </p>
     *
     * @param customerPhone 客户手机号
     * @param orderAmount   订单金额，可选，用于计算优惠金额
     * @return 可用优惠券列表
     */
    @Operation(summary = "获取用户可用优惠券")
    @GetMapping("/available")
    public Result<List<CustomerAvailableCouponResp>> getAvailableCoupons(
            @Parameter(description = "客户手机号") @RequestParam String customerPhone,
            @Parameter(description = "订单金额") @RequestParam(required = false) BigDecimal orderAmount) {
        
        // 1. 根据手机号查找用户
        CustomerUser customer = customerUserService.getOne(
                new LambdaQueryWrapper<CustomerUser>().eq(CustomerUser::getPhone, customerPhone)
        );
        if (customer == null) {
            return Result.success(new ArrayList<>());
        }
        
        // 2. 查询用户未使用且未过期的优惠券
        List<CustomerCoupon> coupons = customerCouponService.list(
                new LambdaQueryWrapper<CustomerCoupon>()
                        .eq(CustomerCoupon::getCustomerId, customer.getId())
                        .eq(CustomerCoupon::getStatus, 0)  // 未使用
                        .ge(CustomerCoupon::getExpireTime, new Date())  // 未过期
        );
        
        if (coupons.isEmpty()) {
            return Result.success(new ArrayList<>());
        }
        
        // 3. 获取优惠券模板信息并计算优惠金额
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        List<CustomerAvailableCouponResp> result = new ArrayList<>();
        
        for (CustomerCoupon coupon : coupons) {
            CouponTemplate template = couponTemplateService.getById(coupon.getTemplateId());
            if (template == null) continue;
            
            CustomerAvailableCouponResp resp = new CustomerAvailableCouponResp();
            resp.setCouponId(coupon.getId());
            resp.setTitle(template.getTitle());
            resp.setType(template.getType());
            resp.setThresholdAmount(template.getThresholdAmount());
            resp.setDiscountAmount(template.getDiscountAmount());
            resp.setDiscountRate(template.getDiscountRate());
            resp.setMaxDiscount(template.getMaxDiscount());
            resp.setExpireTime(coupon.getExpireTime() != null ? sdf.format(coupon.getExpireTime()) : null);
            
            // 计算实际优惠金额
            if (orderAmount != null) {
                BigDecimal discount = calculateDiscount(template, orderAmount);
                resp.setCalculatedDiscount(discount);
                // 判断是否可用（满足门槛）
                resp.setUsable(canUseCoupon(template, orderAmount));
            } else {
                resp.setUsable(true);  // 不传金额时默认可用
            }
            
            result.add(resp);
        }
        
        return Result.success(result);
    }
    
    /**
     * 计算优惠金额
     */
    private BigDecimal calculateDiscount(CouponTemplate template, BigDecimal totalPrice) {
        // 检查门槛
        if (template.getThresholdAmount() != null && totalPrice.compareTo(template.getThresholdAmount()) < 0) {
            return BigDecimal.ZERO;
        }
        
        switch (template.getType()) {
            case 1: // 满减券
            case 3: // 现金券
                return template.getDiscountAmount() != null ? template.getDiscountAmount() : BigDecimal.ZERO;
            case 2: // 折扣券（discountRate存储的是小数，如0.9表示9折）
                if (template.getDiscountRate() != null) {
                    // 优惠金额 = 总价 × (1 - 折扣率)
                    // 例如9折：优惠金额 = 69 × (1 - 0.9) = 69 × 0.1 = 6.9
                    BigDecimal discount = totalPrice.multiply(BigDecimal.ONE.subtract(template.getDiscountRate()));
                    // 如果有最大优惠限制
                    if (template.getMaxDiscount() != null && discount.compareTo(template.getMaxDiscount()) > 0) {
                        return template.getMaxDiscount();
                    }
                    return discount;
                }
                return BigDecimal.ZERO;
            default:
                return BigDecimal.ZERO;
        }
    }
    
    /**
     * 判断优惠券是否可用
     */
    private boolean canUseCoupon(CouponTemplate template, BigDecimal totalPrice) {
        if (template.getThresholdAmount() == null) {
            return true;
        }
        return totalPrice.compareTo(template.getThresholdAmount()) >= 0;
    }
}
