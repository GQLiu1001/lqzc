package com.lqzc.controller;

import com.lqzc.common.Result;
import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.resp.SalesResp;
import com.lqzc.common.resp.SalesTrendResp;
import com.lqzc.service.OrderDetailService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.Resource;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ZSetOperations;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

@Tag(name = "销售统计相关接口")
@RestController
@RequestMapping("/sales")
public class SalesController {
    @Resource
    private OrderDetailService orderDetailService;
    @Resource
    private StringRedisTemplate stringRedisTemplate;
    /**
     * 获取销量前五商品（一周）
     */
    @Operation(summary = "获取一周销量前五商品", description = "获取销量排名前五的商品列表")
    @GetMapping("/top-products")
    public Result<List<SalesResp>> topProducts() {
        // 目前只在redis里查询： to do -》 没有 -》 分布式锁 -》 分布式锁 数据库查询 添加redis（数据与锁） -》 返回
        // 使用 reverseRangeWithScores 获取销量排名前五的商品
        // 0 表示起始索引，4 表示结束索引 (包含)，即获取前5个 ZSet默认升序
        Set<ZSetOperations.TypedTuple<String>> topItems = stringRedisTemplate.opsForZSet()
                .reverseRangeWithScores(RedisConstant.HOT_SALES, 0, 4);

        if (topItems == null || topItems.isEmpty()) {
            return Result.success(new ArrayList<>()); // 如果没有数据。返回空列表
        }
        //forEach
        List<SalesResp> resps = new ArrayList<>();
        topItems.forEach(topItem -> {
            SalesResp resp = new SalesResp();
            resp.setModel(topItem.getValue()); // 商品型号
            // 这里，tuple.getScore() 返回 Double，使用 intValue() 转换为 Integer
            resp.setAmount(topItem.getScore() != null ? topItem.getScore().intValue() : 0);
            resps.add(resp);// Stream map 操作中的“输出”
        });
        // 将查询结果转换为 SalesResp 列表
        //Stream API
        //stream().map()对每个元素应用你指定的一个函数（或逻辑）。根据这个函数的返回值，生成一个新的元素。
        // .collect收集操作 Collectors.toList()
//        List<SalesResp> resps = topItems.stream()
//                .map(tuple -> {
//                    SalesResp resp = new SalesResp();
//                    resp.setModel(tuple.getValue()); // 商品型号
//                    // 这里，tuple.getScore() 返回 Double，使用 intValue() 转换为 Integer
//                    resp.setAmount(tuple.getScore() != null ? tuple.getScore().intValue() : 0);
//                    return resp;// Stream map 操作中的“输出”
//                })
//                .collect(Collectors.toList());

        return Result.success(resps);
    }
    
    /**
     * 获取销售趋势报表（根据当前时间点）
     */
    @Operation(summary = "获取销售趋势报表", description = "根据指定年月获取销售趋势数据")
    @GetMapping("/trend/{year}/{month}/{length}")
    public Result<List<SalesTrendResp>> trend(@Parameter(description = "年份", required = true) @PathVariable Integer year,
                                              @Parameter(description = "月份", required = true) @PathVariable Integer month,
                                              @Parameter(description = "数据长度", required = true) @PathVariable Integer length) {
        List<SalesTrendResp> resp = orderDetailService.topSalesTrend(year, month, length);
        if (resp != null) {
            return Result.success(resp);
        }
        return Result.fail();
    }

//    @Operation(summary = "测试多线程版本")
//    @GetMapping("/trend/{year}/{month}/{length}/test")
//    public Result<List<SalesTrendResp>> trendMul(@Parameter(description = "年份", required = true) @PathVariable Integer year,
//                                              @Parameter(description = "月份", required = true) @PathVariable Integer month,
//                                              @Parameter(description = "数据长度", required = true) @PathVariable Integer length) {
//        List<SalesTrendResp> resp = orderDetailService.topSalesTrendMul(year, month, length);
//        if (resp != null) {
//            return Result.success(resp);
//        }
//        return Result.fail();
//    }
}
