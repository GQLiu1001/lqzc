package com.lqzc.mcp.tool;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.domain.Driver;
import com.lqzc.common.domain.InventoryItem;
import com.lqzc.common.domain.OrderDetail;
import com.lqzc.common.domain.OrderInfo;
import com.lqzc.common.records.MallItemsListRecord;
import com.lqzc.common.resp.MallItemsListResp;
import com.lqzc.mcp.dto.CustomerOrderItem;
import com.lqzc.mcp.dto.InventoryLookupResponse;
import com.lqzc.mcp.dto.LogisticsTraceResponse;
import com.lqzc.mcp.dto.OrderDetailResponse;
import com.lqzc.mcp.dto.TopSalesItem;
import com.lqzc.mcp.support.McpSupport;
import com.lqzc.service.DriverService;
import com.lqzc.service.InventoryItemService;
import com.lqzc.service.OrderDetailService;
import com.lqzc.service.OrderInfoService;
import lombok.RequiredArgsConstructor;
import org.springaicommunity.mcp.annotation.McpTool;
import org.springaicommunity.mcp.annotation.McpToolParam;
import org.springframework.data.geo.Point;
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
    private final DriverService driverService;
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

    @McpTool(
            name = "getCustomerLogisticsTrace",
            description = "根据内部注入的 customerId 和订单号查询订单物流轨迹，返回当前物流状态、司机信息和轨迹时间线"
    )
    public LogisticsTraceResponse getCustomerLogisticsTrace(
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

        Driver driver = order.getDriverId() == null ? null : driverService.getById(order.getDriverId());
        Point driverPoint = resolveDriverPoint(order.getDriverId());

        return new LogisticsTraceResponse(
                order.getOrderNo(),
                order.getOrderStatus(),
                McpSupport.orderStatusLabel(
                        order.getOrderStatus(),
                        order.getDispatchStatus(),
                        order.getCancelReason()
                ),
                order.getDispatchStatus(),
                McpSupport.dispatchStatusLabel(order.getDispatchStatus()),
                resolveLogisticsStatus(order),
                resolveLogisticsMessage(order, driver),
                McpSupport.formatDateTime(order.getExpectedDeliveryTime()),
                McpSupport.formatDateTime(order.getReceiveTime()),
                driver == null ? null : new LogisticsTraceResponse.DriverInfo(
                        driver.getId(),
                        driver.getName(),
                        McpSupport.maskPhone(driver.getPhone()),
                        driver.getWorkStatus(),
                        McpSupport.driverWorkStatusLabel(driver.getWorkStatus())
                ),
                driverPoint == null ? null : new LogisticsTraceResponse.DriverLocation(
                        driverPoint.getY(),
                        driverPoint.getX()
                ),
                buildTimeline(order, driver)
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

    private Point resolveDriverPoint(Long driverId) {
        if (driverId == null || driverId <= 0) {
            return null;
        }
        List<Point> points = stringRedisTemplate.opsForGeo()
                .position(RedisConstant.DRIVER_LOCATION, String.valueOf(driverId));
        if (points == null || points.isEmpty()) {
            return null;
        }
        return points.getFirst();
    }

    private static String resolveLogisticsStatus(OrderInfo order) {
        if (order.getCancelReason() != null && !order.getCancelReason().isBlank()) {
            return "已取消";
        }
        if (order.getOrderStatus() != null && order.getOrderStatus() == 0) {
            return "待支付";
        }
        if (order.getReceiveTime() != null || Integer.valueOf(3).equals(order.getDispatchStatus())) {
            return "已签收";
        }
        if (Integer.valueOf(2).equals(order.getDispatchStatus())) {
            return "派送中";
        }
        if (Integer.valueOf(1).equals(order.getDispatchStatus())) {
            return "待司机接单";
        }
        if (Integer.valueOf(0).equals(order.getDispatchStatus())) {
            return "待派送";
        }
        return McpSupport.orderStatusLabel(order.getOrderStatus(), order.getDispatchStatus(), order.getCancelReason());
    }

    private static String resolveLogisticsMessage(OrderInfo order, Driver driver) {
        if (order.getCancelReason() != null && !order.getCancelReason().isBlank()) {
            return "订单已取消，原因：" + order.getCancelReason();
        }
        if (order.getOrderStatus() != null && order.getOrderStatus() == 0) {
            return "订单尚未支付，物流暂未开始。";
        }
        if (order.getReceiveTime() != null || Integer.valueOf(3).equals(order.getDispatchStatus())) {
            return "订单已签收完成。";
        }
        if (Integer.valueOf(2).equals(order.getDispatchStatus())) {
            return driver == null
                    ? "订单正在派送中。"
                    : "订单正在派送中，司机 " + safeName(driver.getName()) + " 正在配送。";
        }
        if (Integer.valueOf(1).equals(order.getDispatchStatus())) {
            return "订单已进入待接单阶段，正在等待司机接单。";
        }
        if (Integer.valueOf(0).equals(order.getDispatchStatus())) {
            return "订单已支付，等待仓库安排派送。";
        }
        return "物流状态暂未更新，请稍后再试。";
    }

    private static List<LogisticsTraceResponse.TraceEvent> buildTimeline(OrderInfo order, Driver driver) {
        List<LogisticsTraceResponse.TraceEvent> events = new ArrayList<>();
        events.add(new LogisticsTraceResponse.TraceEvent(
                "order_created",
                "订单已创建",
                "订单已生成，等待后续处理。",
                McpSupport.formatDateTime(order.getCreateTime())
        ));

        if (order.getPayTime() != null) {
            events.add(new LogisticsTraceResponse.TraceEvent(
                    "order_paid",
                    "订单已支付",
                    "订单支付成功，进入履约流程。",
                    McpSupport.formatDateTime(order.getPayTime())
            ));
        }

        if (Integer.valueOf(0).equals(order.getDispatchStatus())) {
            events.add(new LogisticsTraceResponse.TraceEvent(
                    "waiting_dispatch",
                    "等待派送",
                    "仓库正在准备派送。",
                    McpSupport.formatDateTime(order.getUpdateTime())
            ));
        }

        if (Integer.valueOf(1).equals(order.getDispatchStatus())) {
            events.add(new LogisticsTraceResponse.TraceEvent(
                    "waiting_driver",
                    "等待司机接单",
                    "订单已放入待接单池，等待司机抢单。",
                    McpSupport.formatDateTime(order.getUpdateTime())
            ));
        }

        if (Integer.valueOf(2).equals(order.getDispatchStatus())) {
            String description = driver == null
                    ? "司机已接单，订单正在派送中。"
                    : "司机 " + safeName(driver.getName()) + " 已接单，订单正在派送中。";
            events.add(new LogisticsTraceResponse.TraceEvent(
                    "dispatching",
                    "派送中",
                    description,
                    McpSupport.formatDateTime(order.getUpdateTime())
            ));
        }

        if (order.getReceiveTime() != null || Integer.valueOf(3).equals(order.getDispatchStatus())) {
            events.add(new LogisticsTraceResponse.TraceEvent(
                    "received",
                    "订单已签收",
                    "收货完成。",
                    McpSupport.formatDateTime(order.getReceiveTime() != null ? order.getReceiveTime() : order.getUpdateTime())
            ));
        }

        if (order.getCancelReason() != null && !order.getCancelReason().isBlank()) {
            events.add(new LogisticsTraceResponse.TraceEvent(
                    "cancelled",
                    "订单已取消",
                    order.getCancelReason(),
                    McpSupport.formatDateTime(order.getUpdateTime())
            ));
        }

        return events;
    }

    private static String safeName(String value) {
        String normalized = McpSupport.normalizeBlank(value);
        return normalized == null ? "配送司机" : normalized;
    }
}
