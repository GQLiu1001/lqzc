"""Mall domain repository — queries lqzc_db (MySQL) through the Java MCP Server.

Direct PostgreSQL access is reserved for agent_db (checkpoint, audit, eval).
Business data (orders, inventory, customers) lives in MySQL and is accessed
via MCP tools wrapping existing Java services.
"""

from __future__ import annotations

from app.mcp import client as mcp_client


async def get_inventory_by_model(model: str) -> dict:
    return await mcp_client.call_tool("getInventoryByModel", {"model": model})


async def get_top_sales() -> list | dict:
    return await mcp_client.call_tool("getTopSales", {})


async def search_inventory(
    current: int = 1,
    size: int = 10,
    category: str | None = None,
    surface: str | None = None,
) -> dict:
    args: dict = {"current": current, "size": size}
    if category:
        args["category"] = category
    if surface:
        args["surface"] = surface
    return await mcp_client.call_tool("searchInventory", args)
