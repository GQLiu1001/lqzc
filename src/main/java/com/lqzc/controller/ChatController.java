package com.lqzc.controller;

import com.lqzc.ai.service.ManualSearchService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

import java.util.Collections;
import java.util.List;

@Slf4j
@RequiredArgsConstructor
@RestController
@RequestMapping("/mall/ai")
public class ChatController {

    private final ChatClient chatClient;
    private final ManualSearchService manualSearchService;

    @GetMapping(value = "/stream-chat", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<String> streamChat(@RequestParam String message,
                                   @RequestParam String sessionId) {
        long ragStart = System.currentTimeMillis();
        log.info(String.valueOf(ragStart));
        List<ManualSearchService.ManualHit> hits;
        try {
            hits = manualSearchService.search(message, 5);
        } catch (Exception e) {
            log.error("[RAG] 手册检索异常", e);
            hits = Collections.emptyList();
        }
        log.info("[RAG] 手册命中 {} 条，耗时 {} ms", hits.size(), System.currentTimeMillis() - ragStart);

        String context = hits.isEmpty()
                ? "未命中知识库。"
                : buildContext(hits);

        return chatClient.prompt()
                .system("你可以使用以下手册片段回答用户问题，请优先依据这些内容作答。如不足以回答，请说明。")
                .user(context)
                .user(message)
                // 关键改动：用原始字符串 "chat_memory_conversation_id" 替代缺失的常量
                .advisors(a -> a.param("chat_memory_conversation_id", sessionId))
                .stream()
                .content();
    }

    private String buildContext(Iterable<com.lqzc.ai.service.ManualSearchService.ManualHit> hits) {
        StringBuilder sb = new StringBuilder("手册片段：\n");
        for (com.lqzc.ai.service.ManualSearchService.ManualHit hit : hits) {
            sb.append("- [")
                    .append(hit.manualId())
                    .append(" #")
                    .append(hit.chunkIndex())
                    .append("] ")
                    .append(hit.content())
                    .append("\n");
        }
        return sb.toString();
    }
}
