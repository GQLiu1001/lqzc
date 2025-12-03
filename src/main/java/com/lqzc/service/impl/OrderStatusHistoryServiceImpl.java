package com.lqzc.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.domain.OrderStatusHistory;
import com.lqzc.mapper.OrderStatusHistoryMapper;
import com.lqzc.service.OrderStatusHistoryService;
import org.springframework.stereotype.Service;

/**
* @author rabbittank
* @description 针对表【order_status_history(订单状态变更记录)】的数据库操作Service实现
* @createDate 2025-07-11 09:05:49
*/
@Service
public class OrderStatusHistoryServiceImpl extends ServiceImpl<OrderStatusHistoryMapper, OrderStatusHistory>
    implements OrderStatusHistoryService{

}



