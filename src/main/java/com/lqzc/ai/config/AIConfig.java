package com.lqzc.ai.config;

import com.alibaba.cloud.ai.memory.jdbc.MysqlChatMemoryRepository;
import com.lqzc.ai.tool.AITools;
import jakarta.annotation.Resource;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.MessageChatMemoryAdvisor;
import org.springframework.ai.chat.client.advisor.SimpleLoggerAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.ai.chat.memory.ChatMemoryRepository;
import org.springframework.ai.chat.memory.MessageWindowChatMemory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.JdbcTemplate;

@Configuration
public class AIConfig {

    // 2. 不再注入具体的 Function，而是注入整个 AITools 服务
    @Resource
    private AITools aiTools;

    @Bean
    public ChatClient chatClient(ChatClient.Builder builder, JdbcTemplate jdbcTemplate) {

        ChatMemoryRepository chatMemoryRepository = MysqlChatMemoryRepository.mysqlBuilder()
                .jdbcTemplate(jdbcTemplate)
                .build();

        ChatMemory chatMemory = MessageWindowChatMemory.builder()
                .chatMemoryRepository(chatMemoryRepository)
                .maxMessages(2000)
                .build();

        return builder
                .defaultSystem(
                        """
                        你是“陶选到家”瓷砖商城的一名金牌销售顾问。
                        你的任务是热情、专业地帮助客户选择瓷砖，解答疑问，并辅助下单。
                        - 当用户询问热销产品或排行榜时，使用queryTopSales工具查询，但是不要告诉用户你准备要用的工具的名字。
                        - 当用户咨询售后政策、保养、安装、清洁或维修相关问题时，先调用searchManualKnowledge工具查询知识库（保养手册、售后指南），基于返回片段总结回答，避免臆造。
                        - 回答售后/保养问题时先给出简短结论，再列出 1-3 条关键要点。
                        - 保持友好和专业的态度，请使用中文回答。
                        - 在回答中可以适当使用 emoji (例如 ✨, 😊, 👍) 来增加亲和力。
                        """
                )
                // 3. 使用 .defaultTools() 并传入整个服务实例。
                // 框架会自动扫描 aiTools 对象中所有被 @Tool 注解的方法。
                .defaultTools(aiTools)
                .defaultAdvisors(
                        new SimpleLoggerAdvisor(),
                        MessageChatMemoryAdvisor.builder(chatMemory).build()
                )
                .build();
    }
}
