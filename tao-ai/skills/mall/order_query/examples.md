# 订单查询示例

## 示例 1：查最近订单
用户：帮我查最近三笔订单
→ 调用 `my_order_query(limit=3)`
→ 回答：列出订单编号、状态、金额

## 示例 2：查订单详情
用户：订单 ORD20250101001 现在什么状态
→ 调用 `order_detail_query(order_no="ORD20250101001")`
→ 回答：订单状态、金额、支付方式、发货时间

## 示例 3：查物流
用户：我的订单什么时候能到
→ 先调用 `my_order_query(limit=1)` 定位最近订单
→ 再调用 `logistics_trace_query(order_no=...)` 查物流
→ 回答：当前物流节点、预计到达时间

## 示例 4：订单+物流组合查询
用户：ORD20250101001 发货了吗，到哪了
→ 同时调用 `order_detail_query` + `logistics_trace_query`
→ 回答：发货状态 + 物流轨迹
