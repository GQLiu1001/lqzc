package com.lqzc.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.domain.InventoryItem;
import com.lqzc.common.domain.InventoryLog;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.common.records.MallItemsListRecord;
import com.lqzc.common.req.ItemsChangeReq;
import com.lqzc.common.req.LogsInboundReq;
import com.lqzc.common.req.OrderNewReq;
import com.lqzc.service.InventoryItemService;
import com.lqzc.mapper.InventoryItemMapper;
import jakarta.annotation.Resource;
import org.springframework.beans.BeanUtils;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.util.Date;
import java.util.List;
import java.util.Objects;

/**
 * @author rabbittank
 * @description 针对表【inventory_item(瓷砖库存表)】的数据库操作Service实现
 * @createDate 2025-07-11 09:05:49
 */
@Service
public class InventoryItemServiceImpl extends ServiceImpl<InventoryItemMapper, InventoryItem>
        implements InventoryItemService {
    @Resource
    private InventoryItemMapper inventoryItemMapper;
    @Resource
    private StringRedisTemplate stringRedisTemplate;

    @Override
    public IPage<InventoryItem> getList(IPage<InventoryItem> page, String category, String surface) {
        return inventoryItemMapper.getList(page, category, surface);
    }

    @Override
    public IPage<MallItemsListRecord> getItemsList(IPage<MallItemsListRecord> page, String category, String surface) {
        return inventoryItemMapper.getItemsList(page, category, surface);
    }

    @Override
    public void itemsChange(ItemsChangeReq request) {
        InventoryItem inventoryItem = inventoryItemMapper.selectById(request.getId());
        BeanUtils.copyProperties(request, inventoryItem);
        inventoryItem.setUpdateTime(new Date());
        inventoryItemMapper.updateById(inventoryItem);
    }

    @Override
    public void postOutboundItem(List<OrderNewReq.OrderNewItem> items) {
        items.forEach(item -> {
            //对子订单每个产品进行出库操作 减库存
            Long itemId = item.getItemId();
            Integer quantity = item.getAmount();
            InventoryItem inventoryItem = inventoryItemMapper.selectById(itemId);
            if (inventoryItem == null || inventoryItem.getTotalAmount() < quantity) {
                // 抛出库存不足或商品不存在的异常
                throw new LianqingException("商品库存不足或商品不存在");
            }
            inventoryItem.setUpdateTime(new Date());
            Integer totalAmount = inventoryItem.getTotalAmount();
            inventoryItem.setTotalAmount(totalAmount - quantity);
            int i = inventoryItemMapper.updateById(inventoryItem);
            if (i == 0) {
                throw new LianqingException("子订单item出库扣减库存失败");
            }
            //Redis 热销榜
            stringRedisTemplate.opsForZSet().add(RedisConstant.HOT_SALES, inventoryItem.getModel(), quantity);
        });
    }

    @Override
    public Long postInboundItem(LogsInboundReq request) {
        LambdaQueryWrapper<InventoryItem> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(InventoryItem::getModel, request.getModel());
        InventoryItem inventoryItem = inventoryItemMapper.selectOne(queryWrapper);

        if (inventoryItem == null) {
            // 如果库存项不存在，则创建新的并插入数据库
            inventoryItem = new InventoryItem();
            BeanUtils.copyProperties(request, inventoryItem); // 将请求参数复制到新对象
            inventoryItem.setCreateTime(new Date());
            inventoryItem.setUpdateTime(new Date());

            int insertedRows = inventoryItemMapper.insert(inventoryItem);
            if (insertedRows == 0) {
                throw new LianqingException("创建新库存项失败，未插入任何记录。");
            }
            return inventoryItem.getId();
        } else {
            // 如果库存项存在，则更新数量
            inventoryItem.setTotalAmount(inventoryItem.getTotalAmount() + request.getTotalAmount());
            inventoryItem.setUpdateTime(new Date()); // *** 修正点：更新现有项的 updateTime ***
            int updatedRows = inventoryItemMapper.updateById(inventoryItem);
            if (updatedRows == 0) {
                // 考虑这里抛出更具体的异常，比如“库存项已存在但更新失败，可能数据冲突”
                throw new LianqingException("未能成功更新现有库存项。");
            }
            return inventoryItem.getId();
        }
    }

    @Override
    public void postTransferItem(Long itemId, Integer sourceWarehouse, Integer targetWarehouse) {
        //只需换下仓库号
        InventoryItem inventoryItem = inventoryItemMapper.selectById(itemId);
        if (inventoryItem == null) {
            throw new RuntimeException();
        }
        if (!Objects.equals(inventoryItem.getWarehouseNum(), sourceWarehouse)) {
            throw new RuntimeException();
        }
        inventoryItem.setWarehouseNum(targetWarehouse);
        int updatedRows = inventoryItemMapper.updateById(inventoryItem);
        if (updatedRows == 0) {
            throw new LianqingException("调拨失败：未能成功更新库存项仓库信息。");
        }
    }

    @Override
    public void itemReversal(InventoryLog inventoryLog) {
        //这里是原本的log原本 +40 入库 -> -40 冲正
        //如果是调库 只需要改Item的仓库名称
        //如果是入库 只需要改Item的数量
        //如果是出库 只需要改Item的数量
        Long inventoryItemId = inventoryLog.getItemId();
        Integer operationType = inventoryLog.getLogType();
        Integer quantityChange = inventoryLog.getAmountChange();
        Integer sourceWarehouse = inventoryLog.getSourceWarehouse();
        Integer updatedRows = inventoryItemMapper.itemReversal(operationType, inventoryItemId, sourceWarehouse, quantityChange);
        if (updatedRows == 0) {
            throw new LianqingException("调拨失败：未能成功更新库存项仓库信息。");
        }
    }

}




