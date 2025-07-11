package com.lqzc.config;

import org.springframework.amqp.core.*;
import org.springframework.amqp.rabbit.config.SimpleRabbitListenerContainerFactory;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.rabbit.listener.RabbitListenerContainerFactory;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {
    // 加钱消息
    public static final String ADD_MONEY_EXCHANGE = "add.money.exchange";
    public static final String ADD_MONEY_QUEUE = "add.money.queue";
    public static final String ADD_MONEY_ROUTING_KEY = "add.money.complete";

    // 加钱交换机
    @Bean
    public DirectExchange addMoneyExchange() {
        return new DirectExchange(ADD_MONEY_EXCHANGE, true, false);
    }

    // 加钱队列
    @Bean
    public Queue addMoneyQueue() {
        return new Queue(ADD_MONEY_QUEUE, true);
    }

    // 加钱绑定
    @Bean
    public Binding addMoneyBinding(Queue addMoneyQueue, DirectExchange addMoneyExchange) {
        return BindingBuilder.bind(addMoneyQueue).to(addMoneyExchange).with(ADD_MONEY_ROUTING_KEY);
    }

    // 改状态消息
    public static final String CHANGE_STATUS_ROUTING_KEY = "change.status.complete";
    public static final String CHANGE_STATUS_EXCHANGE = "change.status.exchange";
    public static final String CHANGE_STATUS_QUEUE = "change.status.queue";

    // 改状态交换机
    @Bean
    public DirectExchange changeStatusExchange() {
        return new DirectExchange(CHANGE_STATUS_EXCHANGE, true, false);
    }

    // 改状态队列
    @Bean
    public Queue changeStatusQueue() {
        return new Queue(CHANGE_STATUS_QUEUE, true);
    }

    // 改状态绑定
    @Bean
    public Binding changeStatusBinding(Queue changeStatusQueue, DirectExchange changeStatusExchange) {
        return BindingBuilder.bind(changeStatusQueue).to(changeStatusExchange).with(CHANGE_STATUS_ROUTING_KEY);
    }

    // RabbitTemplate 配置（用于发送消息）
    @Bean
    public RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory) {
        RabbitTemplate rabbitTemplate = new RabbitTemplate(connectionFactory);
        rabbitTemplate.setMessageConverter(new Jackson2JsonMessageConverter());
        return rabbitTemplate;
    }

    @Bean
    public Jackson2JsonMessageConverter messageConverter() {
        return new Jackson2JsonMessageConverter();
    }

    @Bean
    public RabbitListenerContainerFactory rabbitListenerContainerFactory(ConnectionFactory connectionFactory, Jackson2JsonMessageConverter messageConverter) {
        SimpleRabbitListenerContainerFactory factory = new SimpleRabbitListenerContainerFactory();
        factory.setConnectionFactory(connectionFactory);
        factory.setMessageConverter(messageConverter);
        factory.setAcknowledgeMode(AcknowledgeMode.AUTO); // 手动确认
        return factory;
    }
}