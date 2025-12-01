package com.lqzc.ai.tool;

import com.lqzc.ai.service.ManualSearchService;
import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.resp.SalesResp;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.context.annotation.Description;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ZSetOperations;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;

@Slf4j
@Service // 1. 将 @Configuration 改为 @Service
public class AITools {

    @Resource
    private StringRedisTemplate stringRedisTemplate;
    @Resource
    private ManualSearchService manualSearchService;

    // 请求参数的定义保持不变
    public record TopSalesQueryRequest() {}
    public record ManualSearchRequest(String question) {}

    // 2. 这是一个真正的工具方法，不再是返回 Function 的工厂方法
    @Tool // 3. 明确声明这是一个 AI 工具。框架会扫描到它。
    @Description("查询全局销量最高的5款商品，也称为热销榜。此功能不需要任何参数。")
    public List<SalesResp> queryTopSales(TopSalesQueryRequest request) { // 4. 方法直接返回结果，参数也直接传入
        log.info("AI请求查询全局热销榜...");

        Set<ZSetOperations.TypedTuple<String>> topItems = stringRedisTemplate.opsForZSet()
                .reverseRangeWithScores(RedisConstant.HOT_SALES, 0, 4);

        if (topItems == null || topItems.isEmpty()) {
            return Collections.emptyList();
        }

        List<SalesResp> resps = new ArrayList<>();
        topItems.forEach(topItem -> {
            SalesResp resp = new SalesResp();
            resp.setModel(topItem.getValue());
            resp.setAmount(topItem.getScore() != null ? topItem.getScore().intValue() : 0);
            resps.add(resp);
        });

        log.info("查询到热销榜: {}", resps);
        return resps;
    }

    @Tool
    @Description("从 Milvus 知识库查询售后/保养/安装等手册内容，输入用户问题，返回匹配片段。")
    public List<ManualSearchService.ManualHit> searchManualKnowledge(ManualSearchRequest request) {
        if (request == null || request.question() == null || request.question().isBlank()) {
            return Collections.emptyList();
        }
        log.info("AI请求查询手册知识库: {}", request.question());
        return manualSearchService.search(request.question(), 5);
    }
}
