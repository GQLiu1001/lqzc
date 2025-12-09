package com.lqzc.order.state;

import com.lqzc.common.constant.DispatchConstant;
import com.lqzc.common.domain.LoyaltyPointsAccount;
import com.lqzc.common.domain.LoyaltyPointsLog;
import com.lqzc.common.domain.OrderInfo;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.config.RabbitMQConfig;
import com.lqzc.mapper.OrderInfoMapper;
import com.lqzc.order.OrderContext;
import com.lqzc.order.OrderStateFactory;
import com.lqzc.service.LoyaltyPointsAccountService;
import com.lqzc.service.LoyaltyPointsLogService;
import org.junit.jupiter.api.Test;
import org.springframework.amqp.rabbit.core.RabbitTemplate;

import java.math.BigDecimal;
import java.util.Date;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.atLeastOnce;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class OrderStateTest {

    private final OrderStateFactory factory = new OrderStateFactory();

    @Test
    void dispatchingNextMovesToWaitingConfirmAndSendsMessage() {
        OrderInfo orderInfo = new OrderInfo();
        orderInfo.setId(1L);
        orderInfo.setOrderNo("ORD-001");
        orderInfo.setDispatchStatus(DispatchConstant.DISPATCHING);
        orderInfo.setOrderStatus(1);
        orderInfo.setUpdateTime(new Date());

        OrderInfoMapper orderInfoMapper = mock(OrderInfoMapper.class);
        when(orderInfoMapper.updateById(any(OrderInfo.class))).thenReturn(1);
        LoyaltyPointsAccountService accountService = mock(LoyaltyPointsAccountService.class);
        LoyaltyPointsLogService logService = mock(LoyaltyPointsLogService.class);
        RabbitTemplate rabbitTemplate = mock(RabbitTemplate.class);

        OrderContext context = new OrderContext(orderInfo, orderInfoMapper, accountService, logService, rabbitTemplate);
        OrderState state = factory.getState(orderInfo);

        state.next(context);

        assertEquals(DispatchConstant.FINISH_DISPATCH, orderInfo.getDispatchStatus());
        assertEquals(3, orderInfo.getOrderStatus());
        assertNotNull(orderInfo.getReceiveTime());
        verify(orderInfoMapper, atLeastOnce()).updateById(orderInfo);
        verify(rabbitTemplate).convertAndSend(RabbitMQConfig.ADD_MONEY_EXCHANGE,
                RabbitMQConfig.ADD_MONEY_ROUTING_KEY,
                "ORD-001");
    }

    @Test
    void waitingConfirmConfirmGrantsPointsAndCompletesOrder() {
        OrderInfo orderInfo = new OrderInfo();
        orderInfo.setId(2L);
        orderInfo.setOrderStatus(3);
        orderInfo.setDispatchStatus(DispatchConstant.FINISH_DISPATCH);
        orderInfo.setCustomerId(100L);
        orderInfo.setPayableAmount(BigDecimal.valueOf(25));

        LoyaltyPointsAccount account = new LoyaltyPointsAccount();
        account.setCustomerId(100L);
        account.setBalance(10);
        account.setTotalEarned(10);

        OrderInfoMapper orderInfoMapper = mock(OrderInfoMapper.class);
        when(orderInfoMapper.updateById(any(OrderInfo.class))).thenReturn(1);
        LoyaltyPointsAccountService accountService = mock(LoyaltyPointsAccountService.class);
        when(accountService.getOne(any())).thenReturn(account);
        LoyaltyPointsLogService logService = mock(LoyaltyPointsLogService.class);
        RabbitTemplate rabbitTemplate = mock(RabbitTemplate.class);

        OrderContext context = new OrderContext(orderInfo, orderInfoMapper, accountService, logService, rabbitTemplate);
        OrderState state = factory.getState(orderInfo);

        state.confirm(context);

        assertEquals(4, orderInfo.getOrderStatus());
        assertEquals(35, account.getBalance());
        assertEquals(35, account.getTotalEarned());
        verify(orderInfoMapper).updateById(orderInfo);
        verify(logService).save(any(LoyaltyPointsLog.class));
    }

    @Test
    void completedStateRejectsConfirm() {
        OrderInfo orderInfo = new OrderInfo();
        orderInfo.setOrderStatus(4);
        orderInfo.setDispatchStatus(DispatchConstant.FINISH_DISPATCH);

        OrderInfoMapper orderInfoMapper = mock(OrderInfoMapper.class);
        when(orderInfoMapper.updateById(any(OrderInfo.class))).thenReturn(1);
        OrderContext context = new OrderContext(orderInfo, orderInfoMapper, mock(LoyaltyPointsAccountService.class),
                mock(LoyaltyPointsLogService.class), mock(RabbitTemplate.class));

        OrderState state = factory.getState(orderInfo);

        assertThrows(LianqingException.class, () -> state.confirm(context));
    }
}
