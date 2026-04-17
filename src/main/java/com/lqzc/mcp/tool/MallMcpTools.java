package com.lqzc.mcp.tool;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.domain.InventoryItem;
import com.lqzc.common.domain.OrderDetail;
import com.lqzc.common.domain.OrderInfo;
import com.lqzc.common.records.MallItemsListRecord;
import com.lqzc.common.resp.MallItemsListResp;
import com.lqzc.mcp.dto.CustomerOrderItem;
import com.lqzc.mcp.dto.InventoryLookupResponse;
import com.lqzc.mcp.dto.OrderDetailResponse;
import com.lqzc.mcp.dto.TopSalesItem;
import com.lqzc.mcp.support.McpSupport;
import com.lqzc.service.InventoryItemService;
import com.lqzc.service.OrderDetailService;
import com.lqzc.service.OrderInfoService;
import lombok.RequiredArgsConstructor;
import org.springaicommunity.mcp.annotation.McpTool;
import org.springaicommunity.mcp.annotation.McpToolParam;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ZSetOperations;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class MallMcpTools {

    private static final int DEFAULT_ORDER_LIMIT = 5;
    private static final int MAX_ORDER_LIMIT = 20;

    private final InventoryItemService inventoryItemService;
    private final OrderInfoService orderInfoService;
    private final OrderDetailService orderDetailService;
    private final StringRedisTemplate stringRedisTemplate;

    @McpTool(
            name = "getInventoryByModel",
            description = "根据瓷砖型号查询库存详情，返回库存数量、规格、价格、仓库和分类信息"
    )
    public InventoryLookupResponse getInventoryByModel(
            @McpToolParam(description = "商品型号，例如 TA800-01", required = true)
            String model
    ) {
        String normalizedModel = requireText(model, "model");
        InventoryItem item = inventoryItemService.query()
                .eq("model", normalizedModel)
                .one();

        if (item == null) {
            throw new IllegalStateException("未找到对应库存型号: " + normalizedModel);
        }

        return InventoryLookupResponse.from(item);
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
                McpSupport.normalizeBlank(category),
                McpSupport.normalizeBlank(surface)
        );

        MallItemsListResp resp = new MallItemsListResp();
        resp.setRecords(record.getRecords());
        resp.setTotal(record.getTotal());
        resp.setCurrent(record.getCurrent());
        resp.setSize(record.getSize());
        return resp;
    }

    @McpTool(
            name = "getCustomerOrders",
            description = "根据内部注入的 customerId 查询该客户最近订单列表，支持按状态过滤"
    )
    public List<CustomerOrderItem> getCustomerOrders(
            @McpToolParam(description = "当前对话客户ID，由 FastAPI 运行时上下文注入", required = true)
            Long customerId,
            @McpToolParam(description = "返回条数，默认 5，最大 20", required = false)
            Integer limit,
            @McpToolParam(description = "订单状态筛选，可选", required = false)
            Integer status
    ) {
        validateCustomerId(customerId);

        int safeLimit = limit == null || limit < 1
                ? DEFAULT_ORDER_LIMIT
                : Math.min(limit, MAX_ORDER_LIMIT);

        Page<OrderInfo> page = new Page<>(1, safeLimit);
        LambdaQueryWrapper<OrderInfo> wrapper = new LambdaQueryWrapper<OrderInfo>()
                .eq(OrderInfo::getCustomerId, customerId)
                .eq(status != null, OrderInfo::getOrderStatus, status)
                .orderByDesc(OrderInfo::getCreateTime);

        List<OrderInfo> orders = orderInfoService.page(page, wrapper).getRecords();
        return orders.stream()
                .map(order -> new CustomerOrderItem(
                        order.getOrderNo(),
                        order.getOrderStatus(),
                        CustomerOrderItem.statusLabel(
                                order.getOrderStatus(),
                                order.getDispatchStatus(),
                                order.getCancelReason()
                        ),
                        order.getPayableAmount(),
                        countOrderItems(order.getId()),
                        McpSupport.formatDateTime(order.getCreateTime())
                ))
                .toList();
    }

    @McpTool(
            name = "getCustomerOrderDetail",
            description = "根据内部注入的 customerId 和订单号查询订单详情，返回支付、发货、金额和商品明细"
    )
    public OrderDetailResponse getCustomerOrderDetail(
            @McpToolParam(description = "当前对话客户ID，由 FastAPI 运行时上下文注入", required = true)
            Long customerId,
            @McpToolParam(description = "订单号，例如 ORD202604170001", required = true)
            String orderNo
    ) {
        validateCustomerId(customerId);
        String normalizedOrderNo = requireText(orderNo, "orderNo");

        OrderInfo order = orderInfoService.getOne(new LambdaQueryWrapper<OrderInfo>()
                .eq(OrderInfo::getCustomerId, customerId)
                .eq(OrderInfo::getOrderNo, normalizedOrderNo));

        if (order == null) {
            throw new IllegalStateException("未找到对应订单: " + normalizedOrderNo);
        }

        List<OrderDetail> orderDetails = orderDetailService.list(
                new LambdaQueryWrapper<OrderDetail>().eq(OrderDetail::getOrderId, order.getId())
        );
        Map<Long, InventoryItem> itemMap = orderDetails.isEmpty()
                ? Map.of()
                : inventoryItemService.listByIds(
                        orderDetails.stream().map(OrderDetail::getItemId).toList()
                ).stream().collect(Collectors.toMap(InventoryItem::getId, Function.identity()));

        List<OrderDetailResponse.ItemDetail> items = orderDetails.stream()
                .map(detail -> {
                    InventoryItem item = itemMap.get(detail.getItemId());
                    return new OrderDetailResponse.ItemDetail(
                            item == null ? null : item.getModel(),
                            item == null ? null : item.getSpecification(),
                            detail.getAmount(),
                            item == null ? null : item.getSellingPrice(),
                            detail.getSubtotalPrice()
                    );
                })
                .toList();

        return new OrderDetailResponse(
                order.getOrderNo(),
                order.getOrderStatus(),
                OrderDetailResponse.orderStatusLabel(
                        order.getOrderStatus(),
                        order.getDispatchStatus(),
                        order.getCancelReason()
                ),
                order.getPayStatus(),
                OrderDetailResponse.payStatusLabel(order.getPayStatus()),
                order.getDispatchStatus(),
                OrderDetailResponse.dispatchStatusLabel(order.getDispatchStatus()),
                order.getTotalPrice(),
                order.getPayableAmount(),
                order.getDiscountAmount(),
                order.getDeliveryFee(),
                order.getDeliveryAddress(),
                order.getPointsUsed(),
                McpSupport.formatDateTime(order.getPayTime()),
                McpSupport.formatDateTime(order.getCreateTime()),
                McpSupport.formatDateTime(order.getReceiveTime()),
                order.getRemark(),
                items
        );
    }

    private int countOrderItems(Long orderId) {
        return Math.toIntExact(orderDetailService.count(
                new LambdaQueryWrapper<OrderDetail>().eq(OrderDetail::getOrderId, orderId)
        ));
    }

    private static void validateCustomerId(Long customerId) {
        if (customerId == null || customerId <= 0) {
            throw new IllegalArgumentException("customerId 非法");
        }
    }

    private static String requireText(String value, String fieldName) {
        String normalized = McpSupport.normalizeBlank(value);
        if (normalized == null) {
            throw new IllegalArgumentException(fieldName + " 不能为空");
        }
        return normalized;
    }
}
