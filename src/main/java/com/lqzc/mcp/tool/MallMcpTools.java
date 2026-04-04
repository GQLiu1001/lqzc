package com.lqzc.mcp.tool;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.domain.InventoryItem;
import com.lqzc.common.records.MallItemsListRecord;
import com.lqzc.common.resp.MallItemsListResp;
import com.lqzc.mcp.dto.InventoryLookupResponse;
import com.lqzc.mcp.dto.TopSalesItem;
import com.lqzc.service.InventoryItemService;
import org.springaicommunity.mcp.annotation.McpTool;
import org.springaicommunity.mcp.annotation.McpToolParam;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ZSetOperations;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

@Service
public class MallMcpTools {

    private final InventoryItemService inventoryItemService;
    private final StringRedisTemplate stringRedisTemplate;

    public MallMcpTools(InventoryItemService inventoryItemService, StringRedisTemplate stringRedisTemplate) {
        this.inventoryItemService = inventoryItemService;
        this.stringRedisTemplate = stringRedisTemplate;
    }

    @McpTool(
            name = "getInventoryByModel",
            description = "根据瓷砖型号查询库存详情，返回库存数量、规格、价格、仓库和分类信息"
    )
    public InventoryLookupResponse getInventoryByModel(
            @McpToolParam(description = "商品型号，例如 TA800-01", required = true)
            String model
    ) {
        if (model == null || model.isBlank()) {
            throw new IllegalArgumentException("model 不能为空");
        }
        String normalizedModel = model.trim();
        InventoryItem item = inventoryItemService.query()
                .eq("model", normalizedModel)
                .one();

        if (item == null) {
            throw new IllegalStateException("未找到对应库存型号: " + normalizedModel);
        }

        return InventoryLookupResponse.from(
                item,
                categoryLabel(item.getCategory()),
                surfaceLabel(item.getSurface())
        );
    }

    @McpTool(
            name = "getTopSales",
            description = "查询当前商城热销榜前五商品，返回商品型号和销量"
    )
    public List<TopSalesItem> getTopSales() {
        Set<ZSetOperations.TypedTuple<String>> topItems = stringRedisTemplate.opsForZSet()
                .reverseRangeWithScores(RedisConstant.HOT_SALES, 0, 4);

        if (topItems == null || topItems.isEmpty()) {
            return List.of();
        }

        List<TopSalesItem> result = new ArrayList<>(topItems.size());
        for (ZSetOperations.TypedTuple<String> tuple : topItems) {
            Integer amount = tuple.getScore() == null ? 0 : tuple.getScore().intValue();
            result.add(new TopSalesItem(tuple.getValue(), amount));
        }
        return result;
    }

    @McpTool(
            name = "searchInventory",
            description = "分页查询可售库存商品列表，支持按类别和表面类型筛选，适用于“有什么货/有哪些库存”这类问题"
    )
    public MallItemsListResp searchInventory(
            @McpToolParam(description = "当前页码，默认 1", required = false)
            Integer current,
            @McpToolParam(description = "每页条数，默认 10", required = false)
            Integer size,
            @McpToolParam(description = "商品类别筛选，可选", required = false)
            String category,
            @McpToolParam(description = "商品表面筛选，可选", required = false)
            String surface
    ) {
        int pageNo = (current == null || current < 1) ? 1 : current;
        int pageSize = (size == null || size < 1) ? 10 : size;

        IPage<MallItemsListRecord> page = new Page<>(pageNo, pageSize);
        IPage<MallItemsListRecord> record = inventoryItemService.getItemsList(
                page,
                normalizeBlank(category),
                normalizeBlank(surface)
        );

        MallItemsListResp resp = new MallItemsListResp();
        resp.setRecords(record.getRecords());
        resp.setTotal(record.getTotal());
        resp.setCurrent(record.getCurrent());
        resp.setSize(record.getSize());
        return resp;
    }

    private static String normalizeBlank(String value) {
        if (value == null) {
            return null;
        }
        String normalized = value.trim();
        return normalized.isEmpty() ? null : normalized;
    }

    private static String categoryLabel(Integer category) {
        return switch (category) {
            case 1 -> "墙砖";
            case 2 -> "地砖";
            case 3 -> "胶";
            case 4 -> "洁具";
            default -> "未知";
        };
    }

    private static String surfaceLabel(Integer surface) {
        return switch (surface) {
            case 1 -> "抛光";
            case 2 -> "哑光";
            case 3 -> "釉面";
            case 4 -> "通体大理石";
            case 5 -> "微晶石";
            case 6 -> "岩板";
            default -> "未知";
        };
    }
}
