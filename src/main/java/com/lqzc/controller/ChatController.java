package com.lqzc.controller;

import jakarta.annotation.Resource;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

@Slf4j
@RequiredArgsConstructor
@RestController
@RequestMapping("/mall/ai")
public class ChatController {

    @Resource
    private  ChatClient chatClient;

    @GetMapping(value = "/stream-chat", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<String> streamChat(@RequestParam String message,
                                   @RequestParam String sessionId) {
        return chatClient.prompt()
                .user(message)
                // 关键改动：用原始字符串 "chat_memory_conversation_id" 替代缺失的常量
                .advisors(a -> a.param("chat_memory_conversation_id", sessionId))
                .stream()
                .content();
    }
}