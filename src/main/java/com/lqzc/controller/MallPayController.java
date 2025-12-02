package com.lqzc.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.lqzc.common.Result;
import com.lqzc.common.domain.*;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.common.req.MallPayCreateReq;
import com.lqzc.common.resp.MallPayStatusResp;
import com.lqzc.service.*;
import com.lqzc.utils.UserContextHolder;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Random;

/**
 * C端支付控制器
 * <p>
 * 模拟支付接口，支付成功后使用乐观锁扣减库存
 * </p>
 */
@Tag(name = "C端-支付")
@RestController
@RequestMapping("/mall/pay")
@RequiredArgsConstructor
@Slf4j
public class MallPayController {

    private final OrderInfoService orderInfoService;
    private final OrderDetailService orderDetailService;
    private final OrderStatusHistoryService orderStatusHistoryService;
    private final InventoryItemService inventoryItemService;
    private final InventoryLogService inventoryLogService;
    private final StringRedisTemplate stringRedisTemplate;

    /** 库存占位Redis key前缀 */
    private static final String STOCK_HOLD_KEY = "order:stock:hold:";
    /** 最大重试次数（乐观锁冲突时） */
    private static final int MAX_RETRY = 3;

    @Operation(summary = "发起支付", description = "模拟支付，点击后直接处理支付成功逻辑")
    @PostMapping("/create")
    @Transactional(rollbackFor = Exception.class)
    public Result<Void> create(@RequestBody MallPayCreateReq req) {
        Long customerId = UserContextHolder.getCustomerId();
        
        // 1. 查询订单
        OrderInfo order = orderInfoService.getOne(
                new LambdaQueryWrapper<OrderInfo>()
                        .eq(OrderInfo::getOrderNo, req.getOrderNo())
                        .eq(OrderInfo::getCustomerId, customerId)
        );
        if (order == null) {
            throw new LianqingException("订单不存在");
        }
        
        // 2. 检查订单状态
        if (order.getOrderStatus() != 0) {
            throw new LianqingException("订单状态不可支付");
        }
        if (order.getPayStatus() != 0) {
            throw new LianqingException("订单已支付");
        }
        
        // 3. 扣减库存（使用乐观锁）
        List<OrderDetail> details = orderDetailService.list(
                new LambdaQueryWrapper<OrderDetail>().eq(OrderDetail::getOrderId, order.getId())
        );
        
        for (OrderDetail detail : details) {
            boolean success = deductStockWithRetry(detail.getItemId(), detail.getAmount());
            if (!success) {
                throw new LianqingException("库存扣减失败，请稀释重试");
            }
        }
        
        // 4. 生成出库日志
        for (OrderDetail detail : details) {
            InventoryItem item = inventoryItemService.getById(detail.getItemId());
            if (item != null) {
                InventoryLog logRecord = new InventoryLog();
                logRecord.setItemId(detail.getItemId());
                logRecord.setAmountChange(-detail.getAmount());
                logRecord.setLogType(2); // 出库
                logRecord.setRemark("C端订单支付出库: " + order.getOrderNo() + ", 商品: " + item.getModel());
                logRecord.setCreateTime(new Date());
                inventoryLogService.save(logRecord);
            }
        }
        
        // 5. 更新订单状态
        Integer oldStatus = order.getOrderStatus();
        String transactionNo = generateTransactionNo(req.getChannel());
        
        order.setOrderStatus(1); // 待发货
        order.setPayStatus(1); // 已支付
        order.setPayChannel(req.getChannel());
        order.setPayTime(new Date());
        order.setUpdateTime(new Date());
        orderInfoService.updateById(order);
        
        // 6. 记录状态历史
        saveOrderStatusHistory(order.getId(), oldStatus, 1, "支付成功，支付渠道：" + getChannelName(req.getChannel()));
        
        // 7. 清理库存占位
        releaseStockHold(order, details);
        
        log.info("支付成功: orderNo={}, transactionNo={}, amount={}", 
                order.getOrderNo(), transactionNo, order.getPayableAmount());
        
        return Result.success();
    }

    @Operation(summary = "查询支付状态")
    @GetMapping("/status/{orderNo}")
    public Result<MallPayStatusResp> status(@PathVariable String orderNo) {
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
        
        MallPayStatusResp resp = new MallPayStatusResp();
        resp.setOrderNo(order.getOrderNo());
        resp.setPayStatus(order.getPayStatus());
        resp.setPayTime(order.getPayTime() != null ? sdf.format(order.getPayTime()) : null);
        // 模拟交易号
        if (order.getPayStatus() == 1) {
            resp.setTransactionNo(generateTransactionNo(order.getPayChannel()));
        }
        
        return Result.success(resp);
    }

    /**
     * 使用乐观锁扣减库存（带重试）
     */
    private boolean deductStockWithRetry(Long itemId, int amount) {
        for (int i = 0; i < MAX_RETRY; i++) {
            InventoryItem item = inventoryItemService.getById(itemId);
            if (item == null) {
                throw new LianqingException("商品不存在");
            }
            if (item.getTotalAmount() < amount) {
                throw new LianqingException("商品 " + item.getModel() + " 库存不足");
            }
            
            // 使用乐观锁更新
            boolean success = inventoryItemService.update(
                    new LambdaUpdateWrapper<InventoryItem>()
                            .eq(InventoryItem::getId, itemId)
                            .eq(InventoryItem::getVersion, item.getVersion())
                            .set(InventoryItem::getTotalAmount, item.getTotalAmount() - amount)
                            .set(InventoryItem::getVersion, item.getVersion() + 1)
                            .set(InventoryItem::getUpdateTime, new Date())
            );
            
            if (success) {
                log.info("库存扣减成功: itemId={}, amount={}, newStock={}", 
                        itemId, amount, item.getTotalAmount() - amount);
                return true;
            }
            
            log.warn("乐观锁冲突，重试第{}次: itemId={}", i + 1, itemId);
        }
        
        return false;
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

    private void releaseStockHold(OrderInfo order, List<OrderDetail> details) {
        for (OrderDetail detail : details) {
            String holdKey = STOCK_HOLD_KEY + order.getOrderNo() + ":" + detail.getItemId();
            stringRedisTemplate.delete(holdKey);
        }
    }

    private String generateTransactionNo(Integer channel) {
        String prefix = channel != null && channel == 1 ? "WX" : "ZFB";
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMddHHmmss");
        return prefix + sdf.format(new Date()) + String.format("%04d", new Random().nextInt(10000));
    }

    private String getChannelName(Integer channel) {
        if (channel == null) return "未知";
        return switch (channel) {
            case 1 -> "微信支付";
            case 2 -> "支付宝";
            default -> "其他";
        };
    }
}
