package com.lqzc.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.domain.InventoryItem;
import com.lqzc.common.domain.InventoryLog;
import com.lqzc.common.domain.OrderDetail;
import com.lqzc.common.domain.OrderInfo;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.common.resp.SalesTrendResp;
import com.lqzc.config.ThreadPoolConfig;
import com.lqzc.mapper.InventoryItemMapper;
import com.lqzc.mapper.InventoryLogMapper;
import com.lqzc.mapper.OrderInfoMapper;
import com.lqzc.service.OrderDetailService;
import com.lqzc.mapper.OrderDetailMapper;
import com.lqzc.utils.YearMonthUtil;
import jakarta.annotation.Resource;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.Date;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;

/**
* @author 11965
* @description 针对表【order_detail(订单项表)】的数据库操作Service实现
* @createDate 2025-07-11 09:05:49
*/
@Service
public class OrderDetailServiceImpl extends ServiceImpl<OrderDetailMapper, OrderDetail>
    implements OrderDetailService{
    @Resource
    private OrderDetailMapper orderDetailMapper;
    @Resource
    private InventoryItemMapper inventoryItemMapper;
    @Resource
    private InventoryLogMapper inventoryLogMapper;
    @Resource
    private OrderInfoMapper orderInfoMapper;
    @Resource
    private StringRedisTemplate stringRedisTemplate;
    @Resource
    private ThreadPoolConfig threadPoolConfig;

    //    @Override
//    public List<SalesTrendResp> topSalesTrend(Integer year, Integer month, Integer length) {
//        //填充近5个月的销售额以及销售货量
//        //通过自定义工具类输出一系列日期 5个月
//        List<String> dates = YearMonthUtil.format(year, month, length);
//        List<SalesTrendResp> salesTrendResps = new ArrayList<>();
//        dates.forEach(date -> {
//            //每个月 都分别统计
//            //一个月的销售额
//            //一个月的销售货量
//            SalesTrendResp resp = orderDetailMapper.getTopSalesTrend(date);
//            salesTrendResps.add(resp);
//
//        });
//        return salesTrendResps;
//    }
//      topSalesTrend多线程版本
    public List<SalesTrendResp> topSalesTrend(Integer year, Integer month, Integer length) {
        // 获取需要查询的日期列表
        List<String> dates = YearMonthUtil.format(year, month, length);
        // 为每个月创建异步查询任务
        List<CompletableFuture<SalesTrendResp>> futures = dates.stream()
                //map(f)	把每个元素 x 映射成 f(x)
                .map(date ->
                        CompletableFuture
                                .supplyAsync(
                                        () -> orderDetailMapper.getTopSalesTrend(date), threadPoolConfig.threadPoolExecutor())
                                .handle((result, throwable) -> {
                                    if (throwable != null) {
                                        // 返回默认值，避免整个查询失败
                                        SalesTrendResp defaultResp = new SalesTrendResp();
                                        defaultResp.setTotalPrice(BigDecimal.ZERO);
                                        defaultResp.setTotalAmount(0L);
                                        return defaultResp;
                                    }
                                    return result;
                                }))
                .toList();

        // 等待所有查询完成并收集结果

        return futures.stream()
                .map(CompletableFuture::join)
                .collect(Collectors.toList());
    }


    @Transactional(rollbackFor = Exception.class)
    @Override
    public void changeSubDetail(OrderDetail orderDetail, Integer changeType) {
        OrderDetail originDetail = orderDetailMapper.selectById(orderDetail.getId());
        //根据changeType的不同做出不同的业务方法
        //0 ：修改
        switch (changeType) {
            case 0: {
                //0是对子订单项进行修改 可能修改数量amount或者金额subtotalPrice
                InventoryItem inventoryItem = inventoryItemMapper.selectById(originDetail.getItemId());
                //diffItems origin - new
                Integer diffItems = originDetail.getAmount() - orderDetail.getAmount();

                //先校验 item数量 如果是补货的话
                if (originDetail.getAmount() < orderDetail.getAmount()) {
                    // 比较存量：库存总量是否小于订单增加的数量
                    if (inventoryItem.getTotalAmount() < Math.abs(diffItems)) {
                        throw new LianqingException("存量不足不能修改");
                    }
                }
                //校验补货的可能性后 可以进行操作

                //先对orderDetail表进行修改 直接update
                int i2 = orderDetailMapper.updateById(orderDetail);
                if (i2 == 0) {
                    throw new LianqingException("更新orderDetail失败");
                }

                //再对orderInfo表进行修改 主要改变totalPrice
                //得到修改前后差的money
                //例子: 总300 子100  -> 总320 子120
                BigDecimal diffPrice = originDetail.getSubtotalPrice().subtract(orderDetail.getSubtotalPrice());
                OrderInfo orderInfo = orderInfoMapper.selectById(originDetail.getOrderId());
                //money sub
                orderInfo.setTotalPrice(orderInfo.getTotalPrice().subtract(diffPrice));
                int i1 = orderInfoMapper.updateById(orderInfo);
                if (i1 == 0) {
                    throw new LianqingException("更新orderInfo失败");
                }

                //inventory_item 只需要更新一个total_amount
                //得到修改前后差的amount
                //例子: 仓库200 订单100 -> 仓库180 订单120 补货
                //item add
                inventoryItem.setTotalAmount(inventoryItem.getTotalAmount() + diffItems);
                int i = inventoryItemMapper.updateById(inventoryItem);
                if (i == 0) {
                    throw new LianqingException("更新item失败");
                }

                //inventory_log 插入一条数据
                String model = inventoryItem.getModel();
                Integer warehouseNum = inventoryItem.getWarehouseNum();
                InventoryLog inventoryLog = new InventoryLog();
                inventoryLog.setItemId(inventoryItem.getId());
                inventoryLog.setAmountChange(diffItems);
                inventoryLog.setUpdateTime(new Date());
                inventoryLog.setCreateTime(new Date());
                if (diffItems > 0) {
                    //退货 -> 入库log
                    inventoryLog.setRemark("订单" + orderInfo.getOrderNo() + "中的" + model + "退货 数量为" + diffItems);
                    inventoryLog.setLogType(1);
                    inventoryLog.setTargetWarehouse(warehouseNum);
                } else {
                    //补货 -> 出库log
                    inventoryLog.setRemark("订单" + orderInfo.getOrderNo() + "中的" + model + "补货 数量为" + diffItems);
                    inventoryLog.setLogType(2);
                    inventoryLog.setSourceWarehouse(warehouseNum);
                }
                int insert = inventoryLogMapper.insert(inventoryLog);
                if (insert == 0) {
                    throw new LianqingException("插入log失败");
                }

                try {
                    stringRedisTemplate.opsForZSet().incrementScore(RedisConstant.HOT_SALES, model, -diffItems);
                } catch (Exception e) {
                    throw new RuntimeException(e);
                }
                break;
            }
            //1 ：添加
            case 1: {
                //校验库存够不够
                InventoryItem inventoryItem = inventoryItemMapper.selectById(orderDetail.getItemId());
                if (inventoryItem.getTotalAmount() < orderDetail.getAmount()) {
                    throw new LianqingException("库存不足");
                }

                //库存足够  直接插入一条新数据到 order_detail表
                orderDetail.setCreateTime(new Date());
                orderDetail.setUpdateTime(new Date());
                int i2 = orderDetailMapper.insert(orderDetail);
                if (i2 == 0) {
                    throw new LianqingException("插入orderDetail失败");
                }

                //增加订单total_price 更改 order_info表 直接加钱
                OrderInfo orderInfo = orderInfoMapper.selectById(orderDetail.getOrderId());
                orderInfo.setTotalPrice(orderInfo.getTotalPrice().add(orderDetail.getSubtotalPrice()));
                int i1 = orderInfoMapper.updateById(orderInfo);
                if (i1 == 0) {
                    throw new LianqingException("更新orderInfo失败");
                }

                // 扣减 inventory_item表 的TotalAmount
                inventoryItem.setTotalAmount(inventoryItem.getTotalAmount() - orderDetail.getAmount());
                int i = inventoryItemMapper.updateById(inventoryItem);
                if (i == 0) {
                    throw new LianqingException("更新inventoryItem失败");
                }

                //增加 inventory_log表 出库
                String model = inventoryItem.getModel();
                Integer newAmount = orderDetail.getAmount();
                Integer warehouseNum = inventoryItem.getWarehouseNum();
                InventoryLog inventoryLog = new InventoryLog();
                inventoryLog.setItemId(inventoryItem.getId());
                inventoryLog.setAmountChange(-newAmount);
                inventoryLog.setUpdateTime(new Date());
                inventoryLog.setCreateTime(new Date());
                inventoryLog.setLogType(2);
                inventoryLog.setRemark("订单" + orderInfo.getOrderNo() + "中插入一条子订单" + model + "新加数量为" + newAmount);
                inventoryLog.setSourceWarehouse(warehouseNum);
                int insert = inventoryLogMapper.insert(inventoryLog);
                if (insert == 0) {
                    throw new LianqingException("插入inventoryLog失败");
                }

                try {
                    stringRedisTemplate.opsForZSet().incrementScore(RedisConstant.HOT_SALES, model, newAmount);
                } catch (Exception e) {
                    throw new RuntimeException(e);
                }
                break;
            }
            case 2: {
                //删除子订单项
                //直接删除 order_detail表 相关数据
                InventoryItem inventoryItem = inventoryItemMapper.selectById(orderDetail.getItemId());
                int i2 = orderDetailMapper.deleteById(orderDetail.getId());
                if (i2 == 0) {
                    throw new LianqingException("删除orderDetail失败");
                }

                //减少订单total_price 更改 order_info表 直接减钱
                OrderInfo orderInfo = orderInfoMapper.selectById(orderDetail.getOrderId());
                orderInfo.setTotalPrice(orderInfo.getTotalPrice().subtract(orderDetail.getSubtotalPrice()));
                int i1 = orderInfoMapper.updateById(orderInfo);
                if (i1 == 0) {
                    throw new LianqingException("更新orderInfo失败");
                }

                // 增加 inventory_item表 的TotalAmount
                inventoryItem.setTotalAmount(inventoryItem.getTotalAmount() + orderDetail.getAmount());
                int i = inventoryItemMapper.updateById(inventoryItem);
                if (i == 0) {
                    throw new LianqingException("更新inventoryItem失败");
                }

                //增加 inventory_log表 入库
                String model = inventoryItem.getModel();
                Integer newAmount = orderDetail.getAmount();
                Integer warehouseNum = inventoryItem.getWarehouseNum();
                InventoryLog inventoryLog = new InventoryLog();
                inventoryLog.setItemId(inventoryItem.getId());
                inventoryLog.setAmountChange(newAmount);
                inventoryLog.setUpdateTime(new Date());
                inventoryLog.setCreateTime(new Date());
                inventoryLog.setLogType(1);
                inventoryLog.setRemark("订单" + orderInfo.getOrderNo() + "中删除一条子订单" + model + "删除数量为" + newAmount);
                inventoryLog.setSourceWarehouse(warehouseNum);
                int insert = inventoryLogMapper.insert(inventoryLog);
                if (insert == 0) {
                    throw new LianqingException("插入inventoryLog失败");
                }

                try {
                    stringRedisTemplate.opsForZSet().incrementScore(RedisConstant.HOT_SALES, model, -newAmount);
                } catch (Exception e) {
                    throw new RuntimeException(e);
                }
                break;
            }

            default:
                throw new LianqingException("非法的 changeType");

        }
    }

}




