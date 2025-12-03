package com.lqzc.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.constant.LogConstant;
import com.lqzc.common.domain.InventoryItem;
import com.lqzc.common.domain.InventoryLog;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.common.req.LogsInboundReq;
import com.lqzc.common.req.LogsTransferReq;
import com.lqzc.common.req.OrderNewReq;
import com.lqzc.mapper.InventoryItemMapper;
import com.lqzc.service.InventoryLogService;
import com.lqzc.mapper.InventoryLogMapper;
import jakarta.annotation.Resource;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;

import java.util.Date;
import java.util.List;
import java.util.Objects;

/**
* @author rabbittank
* @description 针对表【inventory_log(库存操作日志表)】的数据库操作Service实现
* @createDate 2025-07-11 09:05:49
*/
@Service
public class InventoryLogServiceImpl extends ServiceImpl<InventoryLogMapper, InventoryLog>
    implements InventoryLogService{

    @Resource
    private InventoryLogMapper inventoryLogMapper;
    @Resource
    private InventoryItemMapper inventoryItemMapper;
    @Override
    public IPage<InventoryLog> getLog(IPage<InventoryLog> page, String startTime, String endTime, Integer logType) {
        return inventoryLogMapper.getLog(page,startTime,endTime,logType);
    }

    public void postInboundLog(LogsInboundReq request, Long itemId) {
        InventoryLog inventoryLog = new InventoryLog();
        BeanUtils.copyProperties(request,inventoryLog);
        inventoryLog.setItemId(itemId);
        inventoryLog.setLogType(LogConstant.INBOUND);
        inventoryLog.setAmountChange(request.getTotalAmount());
        inventoryLog.setTargetWarehouse(request.getWarehouseNum());
        inventoryLog.setCreateTime(new Date());
        inventoryLog.setUpdateTime(new Date());
        int rowsAffected = inventoryLogMapper.insert(inventoryLog);
        if (rowsAffected == 0) {
            throw new LianqingException("创建入库日志失败，未插入任何记录。");
        }
    }

    public void postTransferLog(LogsTransferReq request) {
        LambdaQueryWrapper<InventoryItem> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(InventoryItem::getId, request.getItemId());
        InventoryItem inventoryItem = inventoryItemMapper.selectOne(queryWrapper);
        InventoryLog inventoryLog = new InventoryLog();
        BeanUtils.copyProperties(request,inventoryLog);
        inventoryLog.setAmountChange(inventoryItem.getTotalAmount());
        inventoryLog.setSourceWarehouse(request.getSourceWarehouse());
        inventoryLog.setTargetWarehouse(request.getTargetWarehouse());
        inventoryLog.setCreateTime(new Date());
        inventoryLog.setUpdateTime(new Date());
        inventoryLog.setRemark("物品"+inventoryItem.getId()+"从" +request.getSourceWarehouse() +"转移到"+request.getTargetWarehouse());
        int rowsAffected = inventoryLogMapper.insert(inventoryLog);
        if (rowsAffected == 0) {
            throw new LianqingException("创建调拨日志失败，未插入任何记录。");
        }
    }

    @Override
    public void postOutboundLog(List<OrderNewReq.OrderNewItem> items) {
        items.forEach(item -> {
            Long itemId = item.getItemId();
            //根据itemId获取信息（warehouseNum）
            InventoryItem inventoryItem = inventoryItemMapper.selectById(itemId);
            Integer quantity = item.getAmount();
            Integer sourceWarehouse = inventoryItem.getWarehouseNum();
            //创建要插入的日志
            InventoryLog inventoryLog = new InventoryLog();
            inventoryLog.setItemId(itemId);
            inventoryLog.setLogType(LogConstant.OUTBOUND);
            inventoryLog.setAmountChange(quantity);
            inventoryLog.setSourceWarehouse(sourceWarehouse);
            inventoryLog.setUpdateTime(new Date());
            inventoryLog.setCreateTime(new Date());
            inventoryLog.setRemark(inventoryItem.getModel()+"出库");
            int insert = inventoryLogMapper.insert(inventoryLog);
            if (insert == 0) {
                throw new LianqingException("插入子订单出库log失败");
            }
        });
    }

    @Override
    public void logReversal(InventoryLog inventoryLog) {
        // 提取需要冲正的记录
        Long inventoryItemId = inventoryLog.getItemId();
        Integer quantityChange =inventoryLog.getAmountChange();
        Integer sourceWarehouse =inventoryLog.getSourceWarehouse();
        Integer targetWarehouse =inventoryLog.getTargetWarehouse();
        Integer operationType = inventoryLog.getLogType();
        //新创建冲正记录
        InventoryLog inventoryLog1 = new InventoryLog();
        inventoryLog1.setItemId(inventoryItemId);
        inventoryLog1.setLogType(LogConstant.REVERSAL);
        inventoryLog1.setCreateTime(new Date());
        inventoryLog1.setUpdateTime(new Date());
        inventoryLog1.setRemark("冲正记录");
        //如果是调库 源库目标库调换 数量不变
        if (Objects.equals(operationType, LogConstant.TRANSFER)){
            inventoryLog1.setAmountChange(quantityChange);
            inventoryLog1.setSourceWarehouse(targetWarehouse);
            inventoryLog1.setTargetWarehouse(sourceWarehouse);

        }else {
            //如果是出库 入库 不用改变仓库 数量相反
            inventoryLog1.setAmountChange(-quantityChange);
            inventoryLog1.setTargetWarehouse(targetWarehouse);
            inventoryLog1.setSourceWarehouse(sourceWarehouse);
        }
        int insert = inventoryLogMapper.insert(inventoryLog1);
        if (insert == 0) {
            throw new LianqingException("冲正记录失败");
        }
    }

}




