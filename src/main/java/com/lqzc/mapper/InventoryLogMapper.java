package com.lqzc.mapper;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.InventoryLog;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;

/**
* @author rabbittank
* @description 针对表【inventory_log(库存操作日志表)】的数据库操作Mapper
* @createDate 2025-07-11 09:05:49
* @Entity com.lqzc.common.domain.InventoryLog
*/
public interface InventoryLogMapper extends BaseMapper<InventoryLog> {
    IPage<InventoryLog> getLog(IPage<InventoryLog> page, String startTime, String endTime, Integer logType);
}




