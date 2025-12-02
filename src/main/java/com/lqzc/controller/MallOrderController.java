package com.lqzc.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lqzc.common.PageResp;
import com.lqzc.common.Result;
import com.lqzc.common.domain.*;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.common.req.MallOrderCreateReq;
import com.lqzc.common.req.MallOrderPreviewReq;
import com.lqzc.common.resp.MallOrderDetailResp;
import com.lqzc.common.resp.MallOrderListResp;
import com.lqzc.common.resp.MallOrderPreviewResp;
import com.lqzc.service.*;
import com.lqzc.utils.UserContextHolder;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

/**
 * C端订单控制器
 * <p>
 * 提供订单预览、创建、列表、详情、取消、确认收货等功能
 * 采用下单仅占位、支付成功再扣库存的策略，使用乐观锁防止超卖
 * </p>
 */
@Tag(name = "C端-订单")
@RestController
@RequestMapping("/mall/order")
@RequiredArgsConstructor
@Slf4j
public class MallOrderController {

    private final OrderInfoService orderInfoService;
    private final OrderDetailService orderDetailService;
    private final OrderStatusHistoryService orderStatusHistoryService;
    private final InventoryItemService inventoryItemService;
    private final CustomerAddressService customerAddressService;
    private final CustomerCouponService customerCouponService;
    private final CouponTemplateService couponTemplateService;
    private final LoyaltyPointsAccountService pointsAccountService;
    private final LoyaltyPointsLogService pointsLogService;
    private final CustomerUserService customerUserService;
    private final StringRedisTemplate stringRedisTemplate;

    /** 库存占位Redis key前缀 */
    private static final String STOCK_HOLD_KEY = "order:stock:hold:";
    /** 占位过期时间（分钟） */
    private static final int STOCK_HOLD_EXPIRE_MINUTES = 30;

    @Operation(summary = "订单结算预览", description = "计算金额，自动匹配最佳优惠券")
    @PostMapping("/preview")
    public Result<MallOrderPreviewResp> preview(@RequestBody MallOrderPreviewReq req) {
        Long customerId = UserContextHolder.getCustomerId();
        
        // 计算商品总价
        BigDecimal totalPrice = BigDecimal.ZERO;
        for (MallOrderPreviewReq.OrderItem item : req.getItems()) {
            InventoryItem inventory = inventoryItemService.getById(item.getItemId());
            if (inventory == null) {
                throw new LianqingException("商品不存在: " + item.getItemId());
            }
            BigDecimal subtotal = inventory.getSellingPrice().multiply(BigDecimal.valueOf(item.getAmount()));
            totalPrice = totalPrice.add(subtotal);
        }
        
        // 配送费（简化：暂时免配送费）
        BigDecimal deliveryFee = BigDecimal.ZERO;
        
        // 计算优惠金额
        BigDecimal discountAmount = BigDecimal.ZERO;
        CouponTemplate optimalCoupon = null;
        
        if (req.getCouponId() != null) {
            // 指定优惠券
            CustomerCoupon coupon = customerCouponService.getById(req.getCouponId());
            if (coupon != null && coupon.getStatus() == 0 && coupon.getCustomerId().equals(customerId)) {
                CouponTemplate template = couponTemplateService.getById(coupon.getTemplateId());
                discountAmount = calculateDiscount(template, totalPrice);
                optimalCoupon = template;
            }
        } else {
            // 自动匹配最佳优惠券
            List<CustomerCoupon> availableCoupons = customerCouponService.list(
                    new LambdaQueryWrapper<CustomerCoupon>()
                            .eq(CustomerCoupon::getCustomerId, customerId)
                            .eq(CustomerCoupon::getStatus, 0)
                            .ge(CustomerCoupon::getExpireTime, new Date())
            );
            
            for (CustomerCoupon coupon : availableCoupons) {
                CouponTemplate template = couponTemplateService.getById(coupon.getTemplateId());
                if (template != null && canUseCoupon(template, totalPrice)) {
                    BigDecimal discount = calculateDiscount(template, totalPrice);
                    if (discount.compareTo(discountAmount) > 0) {
                        discountAmount = discount;
                        optimalCoupon = template;
                    }
                }
            }
        }
        
        // 计算积分抵扣
        BigDecimal pointsDeduction = BigDecimal.ZERO;
        if (req.getUsePoints() != null && req.getUsePoints()) {
            LoyaltyPointsAccount account = pointsAccountService.getOne(
                    new LambdaQueryWrapper<LoyaltyPointsAccount>()
                            .eq(LoyaltyPointsAccount::getCustomerId, customerId)
            );
            if (account != null && account.getBalance() != null && account.getBalance() > 0) {
                // 10积分 = 1元
                int maxPointsDeduction = account.getBalance();
                BigDecimal maxDeduction = BigDecimal.valueOf(maxPointsDeduction).divide(BigDecimal.valueOf(10), 2, RoundingMode.DOWN);
                // 积分抵扣不能超过应付金额的20%
                BigDecimal payableBeforePoints = totalPrice.add(deliveryFee).subtract(discountAmount);
                BigDecimal maxAllowed = payableBeforePoints.multiply(BigDecimal.valueOf(0.2));
                pointsDeduction = maxDeduction.min(maxAllowed);
            }
        }
        
        // 计算应付金额
        BigDecimal payableAmount = totalPrice.add(deliveryFee).subtract(discountAmount).subtract(pointsDeduction);
        payableAmount = payableAmount.max(BigDecimal.ZERO);
        
        MallOrderPreviewResp resp = new MallOrderPreviewResp();
        resp.setTotalPrice(totalPrice);
        resp.setDeliveryFee(deliveryFee);
        resp.setDiscountAmount(discountAmount);
        resp.setPointsDeduction(pointsDeduction);
        resp.setPayableAmount(payableAmount);
        
        if (optimalCoupon != null) {
            MallOrderPreviewResp.OptimalCoupon couponInfo = new MallOrderPreviewResp.OptimalCoupon();
            couponInfo.setId(optimalCoupon.getId());
            couponInfo.setTitle(optimalCoupon.getTitle());
            resp.setOptimalCoupon(couponInfo);
        }
        
        return Result.success(resp);
    }

    @Operation(summary = "创建订单", description = "下单仅占位，支付成功后再扣库存")
    @PostMapping("/create")
    @Transactional(rollbackFor = Exception.class)
    public Result<Void> create(@RequestBody MallOrderCreateReq req) {
        Long customerId = UserContextHolder.getCustomerId();
        CustomerUser customer = customerUserService.getById(customerId);
        
        // 1. 验证地址
        CustomerAddress address = customerAddressService.getById(req.getAddressId());
        if (address == null || !address.getCustomerId().equals(customerId)) {
            throw new LianqingException("收货地址不存在");
        }
        
        // 2. 检查库存并占位（不扣减，仅检查）
        List<OrderDetail> orderDetails = new ArrayList<>();
        BigDecimal totalPrice = BigDecimal.ZERO;
        
        for (MallOrderCreateReq.OrderItem item : req.getItems()) {
            InventoryItem inventory = inventoryItemService.getById(item.getItemId());
            if (inventory == null) {
                throw new LianqingException("商品不存在");
            }
            if (inventory.getTotalAmount() < item.getAmount()) {
                throw new LianqingException("商品 " + inventory.getModel() + " 库存不足");
            }
            
            BigDecimal subtotal = inventory.getSellingPrice().multiply(BigDecimal.valueOf(item.getAmount()));
            totalPrice = totalPrice.add(subtotal);
            
            OrderDetail detail = new OrderDetail();
            detail.setItemId(item.getItemId());
            detail.setAmount(item.getAmount());
            detail.setSubtotalPrice(subtotal);
            orderDetails.add(detail);
        }
        
        // 3. 计算优惠
        BigDecimal discountAmount = BigDecimal.ZERO;
        Long couponId = null;
        if (req.getCouponId() != null) {
            CustomerCoupon coupon = customerCouponService.getById(req.getCouponId());
            if (coupon != null && coupon.getStatus() == 0 && coupon.getCustomerId().equals(customerId)) {
                CouponTemplate template = couponTemplateService.getById(coupon.getTemplateId());
                if (canUseCoupon(template, totalPrice)) {
                    discountAmount = calculateDiscount(template, totalPrice);
                    couponId = coupon.getId();
                }
            }
        }
        
        // 4. 计算积分抵扣
        Integer pointsUsed = req.getPointsUsed() != null ? req.getPointsUsed() : 0;
        BigDecimal pointsDeduction = BigDecimal.valueOf(pointsUsed).divide(BigDecimal.valueOf(10), 2, RoundingMode.DOWN);
        
        // 5. 计算应付金额
        BigDecimal payableAmount = totalPrice.subtract(discountAmount).subtract(pointsDeduction);
        payableAmount = payableAmount.max(BigDecimal.ZERO);
        
        // 6. 创建订单
        OrderInfo order = new OrderInfo();
        order.setOrderNo(generateOrderNo());
        order.setCustomerId(customerId);
        order.setCustomerPhone(customer.getPhone());
        order.setOrderSource(1); // 前台商城
        order.setTotalPrice(totalPrice);
        order.setPayableAmount(payableAmount);
        order.setDiscountAmount(discountAmount);
        order.setDispatchStatus(0); // 待派送
        order.setOrderStatus(0); // 待支付
        order.setPayStatus(0); // 未支付
        order.setDeliveryFee(BigDecimal.ZERO);
        order.setAddressId(address.getId());
        order.setDeliveryAddress(buildAddressString(address));
        order.setCouponId(couponId);
        order.setPointsUsed(pointsUsed);
        order.setRemark(req.getRemark());
        order.setVersion(0);
        order.setCreateTime(new Date());
        orderInfoService.save(order);
        
        // 7. 创建订单项
        for (OrderDetail detail : orderDetails) {
            detail.setOrderId(order.getId());
            detail.setVersion(0);
            detail.setCreateTime(new Date());
        }
        orderDetailService.saveBatch(orderDetails);
        
        // 8. 设置库存占位（Redis）
        for (MallOrderCreateReq.OrderItem item : req.getItems()) {
            String holdKey = STOCK_HOLD_KEY + order.getOrderNo() + ":" + item.getItemId();
            stringRedisTemplate.opsForValue().set(holdKey, String.valueOf(item.getAmount()), STOCK_HOLD_EXPIRE_MINUTES, TimeUnit.MINUTES);
        }
        
        // 9. 记录状态历史
        saveOrderStatusHistory(order.getId(), null, 0, "用户下单");
        
        // 10. 锁定优惠券（标记为已使用）
        if (couponId != null) {
            customerCouponService.update(
                    new LambdaUpdateWrapper<CustomerCoupon>()
                            .eq(CustomerCoupon::getId, couponId)
                            .set(CustomerCoupon::getStatus, 1)
                            .set(CustomerCoupon::getUsedOrderId, order.getId())
                            .set(CustomerCoupon::getUseTime, new Date())
            );
        }
        
        // 11. 扣减积分
        if (pointsUsed > 0) {
            deductPoints(customerId, pointsUsed, order.getId());
        }
        
        log.info("订单创建成功: orderNo={}, customerId={}, payableAmount={}", order.getOrderNo(), customerId, payableAmount);
        
        return Result.success();
    }

    @Operation(summary = "订单列表", description = "查询当前用户的订单列表")
    @GetMapping("/list")
    public Result<PageResp<MallOrderListResp>> list(
            @Parameter(description = "状态") @RequestParam(required = false) Integer status,
            @Parameter(description = "页码") @RequestParam(defaultValue = "1") Integer current,
            @Parameter(description = "每页条数") @RequestParam(defaultValue = "10") Integer size) {
        Long customerId = UserContextHolder.getCustomerId();
        
        LambdaQueryWrapper<OrderInfo> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(OrderInfo::getCustomerId, customerId);
        if (status != null) {
            queryWrapper.eq(OrderInfo::getOrderStatus, status);
        }
        queryWrapper.orderByDesc(OrderInfo::getCreateTime);
        
        Page<OrderInfo> page = new Page<>(current, size);
        Page<OrderInfo> orderPage = orderInfoService.page(page, queryWrapper);
        
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        List<MallOrderListResp> records = orderPage.getRecords().stream().map(order -> {
            MallOrderListResp resp = new MallOrderListResp();
            resp.setOrderNo(order.getOrderNo());
            resp.setStatus(order.getOrderStatus());
            resp.setPayableAmount(order.getPayableAmount());
            resp.setCreateTime(order.getCreateTime() != null ? sdf.format(order.getCreateTime()) : null);
            
            // 查询订单项
            List<OrderDetail> details = orderDetailService.list(
                    new LambdaQueryWrapper<OrderDetail>().eq(OrderDetail::getOrderId, order.getId())
            );
            List<MallOrderListResp.OrderItemInfo> items = details.stream().map(detail -> {
                InventoryItem item = inventoryItemService.getById(detail.getItemId());
                MallOrderListResp.OrderItemInfo itemInfo = new MallOrderListResp.OrderItemInfo();
                if (item != null) {
                    itemInfo.setModel(item.getModel());
                    itemInfo.setPicture(item.getPicture());
                }
                itemInfo.setAmount(detail.getAmount());
                return itemInfo;
            }).collect(Collectors.toList());
            resp.setItems(items);
            
            return resp;
        }).collect(Collectors.toList());
        
        PageResp<MallOrderListResp> respPage = new PageResp<>();
        respPage.setTotal(orderPage.getTotal());
        respPage.setRecords(records);
        
        return Result.success(respPage);
    }

    @Operation(summary = "订单详情")
    @GetMapping("/detail/{orderNo}")
    public Result<MallOrderDetailResp> detail(@PathVariable String orderNo) {
        Long customerId = UserContextHolder.getCustomerId();
        
        OrderInfo order = orderInfoService.getOne(
                new LambdaQueryWrapper<OrderInfo>()
                        .eq(OrderInfo::getOrderNo, orderNo)
                        .eq(OrderInfo::getCustomerId, customerId)
        );
        if (order == null) {
            throw new LianqingException("订单不存在");
        }
        
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        
        MallOrderDetailResp resp = new MallOrderDetailResp();
        resp.setId(order.getId());
        resp.setOrderNo(order.getOrderNo());
        resp.setCustomerId(order.getCustomerId());
        resp.setCustomerPhone(order.getCustomerPhone());
        resp.setOrderSource(order.getOrderSource());
        resp.setTotalPrice(order.getTotalPrice());
        resp.setPayableAmount(order.getPayableAmount());
        resp.setDiscountAmount(order.getDiscountAmount());
        resp.setDispatchStatus(order.getDispatchStatus());
        resp.setOrderStatus(order.getOrderStatus());
        resp.setPayStatus(order.getPayStatus());
        resp.setPayChannel(order.getPayChannel());
        resp.setPayTime(order.getPayTime() != null ? sdf.format(order.getPayTime()) : null);
        resp.setDeliveryFee(order.getDeliveryFee());
        resp.setCouponId(order.getCouponId());
        resp.setPointsUsed(order.getPointsUsed());
        resp.setRemark(order.getRemark());
        resp.setCreateTime(order.getCreateTime() != null ? sdf.format(order.getCreateTime()) : null);
        resp.setReceiveTime(order.getReceiveTime() != null ? sdf.format(order.getReceiveTime()) : null);
        
        // 地址信息
        CustomerAddress address = customerAddressService.getById(order.getAddressId());
        if (address != null) {
            MallOrderDetailResp.AddressInfo addressInfo = new MallOrderDetailResp.AddressInfo();
            addressInfo.setReceiverName(address.getReceiverName());
            addressInfo.setReceiverPhone(address.getReceiverPhone());
            addressInfo.setProvince(address.getProvince());
            addressInfo.setCity(address.getCity());
            addressInfo.setDistrict(address.getDistrict());
            addressInfo.setDetail(address.getDetail());
            resp.setAddress(addressInfo);
        }
        
        // 订单项
        List<OrderDetail> details = orderDetailService.list(
                new LambdaQueryWrapper<OrderDetail>().eq(OrderDetail::getOrderId, order.getId())
        );
        List<MallOrderDetailResp.OrderItemDetail> items = details.stream().map(detail -> {
            InventoryItem item = inventoryItemService.getById(detail.getItemId());
            MallOrderDetailResp.OrderItemDetail itemDetail = new MallOrderDetailResp.OrderItemDetail();
            itemDetail.setId(detail.getId());
            itemDetail.setItemId(detail.getItemId());
            if (item != null) {
                itemDetail.setModel(item.getModel());
                itemDetail.setSpecification(item.getSpecification());
                itemDetail.setSellingPrice(item.getSellingPrice());
            }
            itemDetail.setAmount(detail.getAmount());
            itemDetail.setSubtotalPrice(detail.getSubtotalPrice());
            return itemDetail;
        }).collect(Collectors.toList());
        resp.setItems(items);
        
        // 状态历史
        List<OrderStatusHistory> histories = orderStatusHistoryService.list(
                new LambdaQueryWrapper<OrderStatusHistory>()
                        .eq(OrderStatusHistory::getOrderId, order.getId())
                        .orderByAsc(OrderStatusHistory::getCreateTime)
        );
        List<MallOrderDetailResp.StatusHistoryItem> statusHistory = histories.stream().map(h -> {
            MallOrderDetailResp.StatusHistoryItem historyItem = new MallOrderDetailResp.StatusHistoryItem();
            historyItem.setFromStatus(h.getFromStatus());
            historyItem.setToStatus(h.getToStatus());
            historyItem.setRemark(h.getRemark());
            historyItem.setCreateTime(h.getCreateTime() != null ? sdf.format(h.getCreateTime()) : null);
            return historyItem;
        }).collect(Collectors.toList());
        resp.setStatusHistory(statusHistory);
        
        return Result.success(resp);
    }

    @Operation(summary = "取消订单", description = "仅限未支付或未发货订单")
    @PostMapping("/cancel/{orderNo}")
    @Transactional(rollbackFor = Exception.class)
    public Result<Void> cancel(
            @PathVariable String orderNo,
            @Parameter(description = "取消原因") @RequestParam(required = false) String reason) {
        Long customerId = UserContextHolder.getCustomerId();
        
        OrderInfo order = orderInfoService.getOne(
                new LambdaQueryWrapper<OrderInfo>()
                        .eq(OrderInfo::getOrderNo, orderNo)
                        .eq(OrderInfo::getCustomerId, customerId)
        );
        if (order == null) {
            throw new LianqingException("订单不存在");
        }
        
        // 只有待支付(0)或待发货(1)的订单可以取消
        if (order.getOrderStatus() != 0 && order.getOrderStatus() != 1) {
            throw new LianqingException("当前订单状态不可取消");
        }
        
        Integer oldStatus = order.getOrderStatus();
        
        // 更新订单状态为已取消
        order.setOrderStatus(4); // 已取消
        order.setCancelReason(reason);
        order.setUpdateTime(new Date());
        orderInfoService.updateById(order);
        
        // 记录状态历史
        saveOrderStatusHistory(order.getId(), oldStatus, 4, "用户取消订单" + (reason != null ? ": " + reason : ""));
        
        // 释放库存占位
        releaseStockHold(order);
        
        // 如果已使用优惠券，退还优惠券
        if (order.getCouponId() != null) {
            customerCouponService.update(
                    new LambdaUpdateWrapper<CustomerCoupon>()
                            .eq(CustomerCoupon::getId, order.getCouponId())
                            .set(CustomerCoupon::getStatus, 0)
                            .set(CustomerCoupon::getUsedOrderId, null)
                            .set(CustomerCoupon::getUseTime, null)
            );
        }
        
        // 如果已使用积分，退还积分
        if (order.getPointsUsed() != null && order.getPointsUsed() > 0) {
            refundPoints(order.getCustomerId(), order.getPointsUsed(), order.getId());
        }
        
        log.info("订单取消成功: orderNo={}", orderNo);
        
        return Result.success();
    }

    @Operation(summary = "确认收货", description = "订单完成，触发积分发放（1元=1积分）")
    @PostMapping("/confirm/{orderNo}")
    @Transactional(rollbackFor = Exception.class)
    public Result<Map<String, Object>> confirm(@PathVariable String orderNo) {
        Long customerId = UserContextHolder.getCustomerId();
        
        OrderInfo order = orderInfoService.getOne(
                new LambdaQueryWrapper<OrderInfo>()
                        .eq(OrderInfo::getOrderNo, orderNo)
                        .eq(OrderInfo::getCustomerId, customerId)
        );
        if (order == null) {
            throw new LianqingException("订单不存在");
        }
        
        // 只有待确认(3)的订单可以确认收货
        if (order.getOrderStatus() != 3) {
            throw new LianqingException("当前订单状态不可确认收货，请等待司机送达");
        }
        
        Integer oldStatus = order.getOrderStatus();
        
        // 更新订单状态为已完成(4)
        order.setOrderStatus(4); // 已完成
        order.setReceiveTime(new Date());
        order.setUpdateTime(new Date());
        orderInfoService.updateById(order);
        
        // 记录状态历史
        saveOrderStatusHistory(order.getId(), oldStatus, 4, "用户确认收货");
        
        // 发放积分（1元=1积分，去除小数点）
        int pointsEarned = order.getPayableAmount().intValue();
        if (pointsEarned > 0) {
            addPoints(customerId, pointsEarned, order.getId(), "订单完成赠送积分");
        }
        
        log.info("订单确认收货成功: orderNo={}, pointsEarned={}", orderNo, pointsEarned);
        
        Map<String, Object> result = new HashMap<>();
        result.put("points_earned", pointsEarned);
        return Result.success(result);
    }

    // ==================== 辅助方法 ====================

    private String generateOrderNo() {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd");
        return "ORD" + sdf.format(new Date()) + String.format("%04d", new Random().nextInt(10000));
    }

    private String buildAddressString(CustomerAddress address) {
        return address.getProvince() + address.getCity() + address.getDistrict() + address.getDetail();
    }

    private boolean canUseCoupon(CouponTemplate template, BigDecimal totalPrice) {
        if (template == null) return false;
        if (template.getThresholdAmount() != null && totalPrice.compareTo(template.getThresholdAmount()) < 0) {
            return false;
        }
        Date now = new Date();
        if (template.getValidFrom() != null && now.before(template.getValidFrom())) return false;
        if (template.getValidTo() != null && now.after(template.getValidTo())) return false;
        return true;
    }

    private BigDecimal calculateDiscount(CouponTemplate template, BigDecimal totalPrice) {
        if (template == null) return BigDecimal.ZERO;
        
        switch (template.getType()) {
            case 1: // 满减
                return template.getDiscountAmount() != null ? template.getDiscountAmount() : BigDecimal.ZERO;
            case 2: // 折扣
                if (template.getDiscountRate() != null) {
                    BigDecimal discount = totalPrice.multiply(BigDecimal.ONE.subtract(template.getDiscountRate()));
                    if (template.getMaxDiscount() != null) {
                        discount = discount.min(template.getMaxDiscount());
                    }
                    return discount;
                }
                return BigDecimal.ZERO;
            case 3: // 现金券
                return template.getDiscountAmount() != null ? template.getDiscountAmount() : BigDecimal.ZERO;
            default:
                return BigDecimal.ZERO;
        }
    }

    private void saveOrderStatusHistory(Long orderId, Integer fromStatus, Integer toStatus, String remark) {
        OrderStatusHistory history = new OrderStatusHistory();
        history.setOrderId(orderId);
        history.setFromStatus(fromStatus);
        history.setToStatus(toStatus);
        history.setRemark(remark);
        history.setCreateTime(new Date());
        orderStatusHistoryService.save(history);
    }

    private void releaseStockHold(OrderInfo order) {
        // 释放Redis中的库存占位
        List<OrderDetail> details = orderDetailService.list(
                new LambdaQueryWrapper<OrderDetail>().eq(OrderDetail::getOrderId, order.getId())
        );
        for (OrderDetail detail : details) {
            String holdKey = STOCK_HOLD_KEY + order.getOrderNo() + ":" + detail.getItemId();
            stringRedisTemplate.delete(holdKey);
        }
    }

    private void deductPoints(Long customerId, int points, Long orderId) {
        LoyaltyPointsAccount account = pointsAccountService.getOne(
                new LambdaQueryWrapper<LoyaltyPointsAccount>()
                        .eq(LoyaltyPointsAccount::getCustomerId, customerId)
        );
        if (account == null || account.getBalance() < points) {
            throw new LianqingException("积分不足");
        }
        
        account.setBalance(account.getBalance() - points);
        account.setTotalSpent((account.getTotalSpent() != null ? account.getTotalSpent() : 0) + points);
        account.setUpdateTime(new Date());
        pointsAccountService.updateById(account);
        
        // 记录流水
        LoyaltyPointsLog log = new LoyaltyPointsLog();
        log.setCustomerId(customerId);
        log.setChangeAmount(-points);
        log.setBalanceAfter(account.getBalance());
        log.setSourceType(3); // 支付抵扣
        log.setOrderId(orderId);
        log.setRemark("支付抵扣积分");
        log.setCreateTime(new Date());
        pointsLogService.save(log);
    }

    private void refundPoints(Long customerId, int points, Long orderId) {
        LoyaltyPointsAccount account = pointsAccountService.getOne(
                new LambdaQueryWrapper<LoyaltyPointsAccount>()
                        .eq(LoyaltyPointsAccount::getCustomerId, customerId)
        );
        if (account == null) return;
        
        account.setBalance(account.getBalance() + points);
        account.setTotalSpent((account.getTotalSpent() != null ? account.getTotalSpent() : 0) - points);
        account.setUpdateTime(new Date());
        pointsAccountService.updateById(account);
        
        // 记录流水
        LoyaltyPointsLog log = new LoyaltyPointsLog();
        log.setCustomerId(customerId);
        log.setChangeAmount(points);
        log.setBalanceAfter(account.getBalance());
        log.setSourceType(2); // 退款回退
        log.setOrderId(orderId);
        log.setRemark("订单取消退还积分");
        log.setCreateTime(new Date());
        pointsLogService.save(log);
    }

    private void addPoints(Long customerId, int points, Long orderId, String remark) {
        LoyaltyPointsAccount account = pointsAccountService.getOne(
                new LambdaQueryWrapper<LoyaltyPointsAccount>()
                        .eq(LoyaltyPointsAccount::getCustomerId, customerId)
        );
        if (account == null) {
            account = new LoyaltyPointsAccount();
            account.setCustomerId(customerId);
            account.setBalance(0);
            account.setTotalEarned(0);
            account.setTotalSpent(0);
            account.setFrozen(0);
            account.setCreateTime(new Date());
            pointsAccountService.save(account);
        }
        
        account.setBalance(account.getBalance() + points);
        account.setTotalEarned((account.getTotalEarned() != null ? account.getTotalEarned() : 0) + points);
        account.setUpdateTime(new Date());
        pointsAccountService.updateById(account);
        
        // 记录流水
        LoyaltyPointsLog log = new LoyaltyPointsLog();
        log.setCustomerId(customerId);
        log.setChangeAmount(points);
        log.setBalanceAfter(account.getBalance());
        log.setSourceType(1); // 下单赠送
        log.setOrderId(orderId);
        log.setRemark(remark);
        log.setCreateTime(new Date());
        pointsLogService.save(log);
    }
}
