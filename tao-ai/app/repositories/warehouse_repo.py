"""Warehouse domain repository.

Business data (inventory, logs) lives in MySQL and is accessed via MCP tools
wrapping existing Java services. Approval records are persisted to agent_db
(PostgreSQL) once the repository layer is fully connected.
"""

from __future__ import annotations

from app.mcp import client as mcp_client


async def get_inventory_by_model(model: str) -> dict:
    return await mcp_client.call_tool("getInventoryByModel", {"model": model})
