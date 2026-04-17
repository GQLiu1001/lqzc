"""Inventory subagent — low-risk, query-only warehouse operations.

Handles: inventory lookup, stock levels, inventory logs, anomaly analysis.
Does NOT handle: outbound applications, approval flows, or any write operations.
"""

from __future__ import annotations

from deepagents.middleware.subagents import SubAgent

from app.tools.warehouse_tools import inventory_log_query, inventory_query


def build_inventory_subagent() -> SubAgent:
    return SubAgent(
        name="warehouse_inventory_subagent",
        description="处理库存查询、库位查询、库存流水和库存异常分析相关问题。不处理出库申请或审批。",
        system_prompt="""\
你是仓储库存专家。
只处理库存、库位、库存日志、库存波动分析相关问题。
不要处理出库审批、仓储执行申请等高风险操作。
优先调用库存相关工具，不要编造库存数据。

工具使用指引：
1. 查某仓某商品库存 → inventory_query(warehouse_id, item_id)
2. 查近 N 天出入库流水 → inventory_log_query(warehouse_id, item_id, days)
3. 判断库存异常时，先查当前库存再查流水做对比分析
4. 查询失败时如实告知，不要编造数据""",
        tools=[inventory_query, inventory_log_query],
        skills=[
            "/skills/shared/response_format/",
            "/skills/warehouse/inventory_query/",
        ],
    )
