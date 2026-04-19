---
name: inventory_query
description: 处理仓储库存查询、库存流水、库存异常分析等只读查询类问题
---

# 库存查询技能

## 适用问题
- "2号仓 itemId=4 还有多少库存"
- "最近 7 天这条 SKU 有没有明显波动"
- "最近一次出库是什么时候"
- "库存是不是异常减少了"
- "这个型号在哪个仓"

## 工具使用指引

### 查当前库存
调用 `inventory_query(warehouse_id, item_id)` 获取指定仓库下某商品的当前库存数量。

### 查库存流水
调用 `inventory_log_query(warehouse_id, item_id, days=7)` 获取近 N 天的出入库记录。

### 判断库存异常
需要组合调用：
1. 先用 `inventory_query` 获取当前库存
2. 再用 `inventory_log_query` 获取近期流水
3. 对比分析是否存在异常减少或激增

## 权限约束
- 只允许查询当前角色 warehouse_scope 内的仓库数据
- 工具内部自动从 runtime context 读取权限范围
- 不允许查询其他角色或租户的仓库数据
- 查询无结果时如实返回，不编造库存数据

## 回答格式
- 库存数量为整数
- 仓库使用"X号仓"格式
- 流水类型使用中文（入库/出库/调拨/冲正）

参考指标定义见 [metrics.md](metrics.md)
