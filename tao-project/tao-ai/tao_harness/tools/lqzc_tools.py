"""Tool builders for lqzc-specific APIs and local knowledge."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from tao_harness.config import settings
from tao_harness.knowledge.manual_search import LocalManualSearch
from tao_harness.knowledge.skill_loader import SkillLoader
from tao_harness.tools.base import ToolDefinition
from tao_harness.tools.mcp_client import LQZCMcpClient
from tao_harness.tools.registry import ToolRegistry


logger = logging.getLogger(__name__)

_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")
_MODEL_LIKE = re.compile(r"^[A-Za-z]{1,6}[0-9]{2,}[A-Za-z0-9-]*$")


def _preview(value: Any, limit: int = 240) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False)
    except TypeError:
        text = str(value)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "..."


class LQZCApiClient:
    """Small HTTP client for the existing Java business system."""

    def __init__(
        self,
        base_url: str,
        customer_token: str = "",
        mcp_client: LQZCMcpClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.customer_token = customer_token
        self.mcp_client = mcp_client

    async def _get(
        self,
        path: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        request_headers = headers or {}
        logger.info(
            "lqzc.http.get.request path=%s params=%s has_token=%s",
            path,
            _preview(params or {}),
            "X-Customer-Token" in request_headers,
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}{path}",
                headers=request_headers,
                params=params,
            )
            logger.info(
                "lqzc.http.get.response path=%s status=%s body=%s",
                path,
                response.status_code,
                _preview(response.text),
            )
            response.raise_for_status()
            return response.json()

    async def get_top_sales(self) -> Any:
        logger.info("lqzc.tool.get_top_sales.request")
        if self.mcp_client is None:
            return {
                "code": 503,
                "message": "MCP 未启用",
                "data": None,
                "hint": "请设置 LQZC_MCP_ENABLED=true，并配置 LQZC_MCP_URL",
            }

        try:
            data = await self.mcp_client.call_tool("getTopSales")
            normalized = self._normalize_mcp_data(data)
            logger.info("lqzc.tool.get_top_sales.response data=%s", _preview(normalized))
            return {"code": 200, "message": "成功", "data": normalized}
        except Exception as exc:
            logger.warning("MCP getTopSales failed: %s", exc)
            return {
                "code": 502,
                "message": "调用 MCP getTopSales 失败",
                "data": None,
                "error": str(exc),
            }

    async def get_coupon_market(self) -> Any:
        headers: dict[str, str] = {}
        if self.customer_token:
            headers["X-Customer-Token"] = self.customer_token
        return await self._get("/mall/coupon/market", headers=headers)

    async def get_inventory_by_model(self, model: str) -> Any:
        logger.info("lqzc.tool.get_inventory_by_model.request model=%s", _preview(model))
        if self.mcp_client is None:
            return {
                "code": 503,
                "message": "MCP 未启用",
                "data": None,
                "hint": "请设置 LQZC_MCP_ENABLED=true，并配置 LQZC_MCP_URL",
            }

        try:
            data = await self.mcp_client.call_tool(
                "getInventoryByModel",
                {"model": model},
            )
            normalized = self._normalize_mcp_data(data)
            logger.info(
                "lqzc.tool.get_inventory_by_model.response model=%s data=%s",
                _preview(model),
                _preview(normalized),
            )
            return {"code": 200, "message": "成功", "data": normalized}
        except Exception as exc:
            logger.warning("MCP getInventoryByModel failed: %s", exc)
            return {
                "code": 502,
                "message": "调用 MCP getInventoryByModel 失败",
                "data": None,
                "error": str(exc),
            }

    async def search_inventory(
        self,
        current: int = 1,
        size: int = 10,
        category: str | None = None,
        surface: str | None = None,
    ) -> Any:
        if self.mcp_client is None:
            return {
                "code": 503,
                "message": "MCP 未启用",
                "data": None,
                "hint": "请设置 LQZC_MCP_ENABLED=true，并配置 LQZC_MCP_URL",
            }

        # Defensive fallback: some models may route exact item model queries
        # (like A8001/B6002) into search_inventory by mistake.
        # If category looks like a model, redirect to exact model lookup.
        if category and _MODEL_LIKE.fullmatch(category.strip()):
            logger.info(
                "lqzc.tool.search_inventory.redirect_to_model category=%s",
                _preview(category),
            )
            return await self.get_inventory_by_model(category.strip())

        params: dict[str, Any] = {
            "current": current,
            "size": size,
        }
        if category:
            params["category"] = category
        if surface:
            params["surface"] = surface
        logger.info(
            "lqzc.tool.search_inventory.request current=%s size=%s category=%s surface=%s",
            current,
            size,
            _preview(category or ""),
            _preview(surface or ""),
        )
        try:
            data = await self.mcp_client.call_tool("searchInventory", params)
            normalized = self._normalize_mcp_data(data)
            logger.info("lqzc.tool.search_inventory.response data=%s", _preview(normalized))
            return {"code": 200, "message": "成功", "data": normalized}
        except Exception as exc:
            logger.warning("MCP searchInventory failed: %s", exc)
            return {
                "code": 502,
                "message": "调用 MCP searchInventory 失败",
                "data": None,
                "error": str(exc),
            }

    async def get_order_detail(self, order_no: str) -> Any:
        logger.info("lqzc.tool.get_order_detail.request order_no=%s", _preview(order_no))
        if not self.customer_token:
            return {
                "error": "LQZC_CUSTOMER_TOKEN is not configured",
                "hint": "Set LQZC_CUSTOMER_TOKEN in .env before using get_order_detail",
            }
        headers = {"X-Customer-Token": self.customer_token}
        return await self._get(f"/mall/order/detail/{order_no}", headers=headers)

    def _normalize_mcp_data(self, data: Any) -> Any:
        if isinstance(data, list):
            return [self._normalize_mcp_data(item) for item in data]
        if isinstance(data, dict):
            return {
                self._to_snake_case(key): self._normalize_mcp_data(value)
                for key, value in data.items()
            }
        return data

    @staticmethod
    def _to_snake_case(value: str) -> str:
        return _CAMEL_BOUNDARY.sub("_", value).lower()


def build_default_registry() -> ToolRegistry:
    """Assemble all tools for the first harness version."""

    registry = ToolRegistry()
    mcp_client = None
    if settings.lqzc_mcp_enabled:
        mcp_client = LQZCMcpClient(settings.lqzc_mcp_url)
    api_client = LQZCApiClient(
        base_url=settings.lqzc_base_url,
        customer_token=settings.lqzc_customer_token,
        mcp_client=mcp_client,
    )
    manual_search = LocalManualSearch(settings.manuals_dir)
    skill_loader = SkillLoader(settings.skills_dir)

    registry.register(
        ToolDefinition(
            name="get_top_sales",
            description="Get the current top selling products from the lqzc backend.",
            input_schema={"type": "object", "properties": {}},
            handler=api_client.get_top_sales,
        )
    )

    registry.register(
        ToolDefinition(
            name="get_coupon_market",
            description="List coupon market entries that are currently available in the mall.",
            input_schema={"type": "object", "properties": {}},
            handler=api_client.get_coupon_market,
        )
    )

    registry.register(
        ToolDefinition(
            name="get_inventory_by_model",
            description="Look up one inventory item by exact model (such as A8001 or B6002) and return stock count, warehouse, price, and basic product details.",
            input_schema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Exact product model, such as a SKU or tile model number.",
                    }
                },
                "required": ["model"],
            },
            handler=api_client.get_inventory_by_model,
        )
    )

    registry.register(
        ToolDefinition(
            name="search_inventory",
            description="Browse a public inventory list by broad filters (category/surface). Do not use for exact model queries like A8001/B6002; use get_inventory_by_model for those.",
            input_schema={
                "type": "object",
                "properties": {
                    "current": {
                        "type": "integer",
                        "description": "Page number. Defaults to 1.",
                        "default": 1,
                    },
                    "size": {
                        "type": "integer",
                        "description": "Page size. Defaults to 10.",
                        "default": 10,
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category filter.",
                    },
                    "surface": {
                        "type": "string",
                        "description": "Optional surface filter.",
                    },
                },
            },
            handler=api_client.search_inventory,
        )
    )

    registry.register(
        ToolDefinition(
            name="get_order_detail",
            description="Get one order detail by order number. Requires LQZC_CUSTOMER_TOKEN.",
            input_schema={
                "type": "object",
                "properties": {
                    "order_no": {
                        "type": "string",
                        "description": "The order number shown in the mall order list",
                    }
                },
                "required": ["order_no"],
            },
            handler=api_client.get_order_detail,
        )
    )

    registry.register(
        ToolDefinition(
            name="search_local_manuals",
            description="Search local after-sales, maintenance, and installation manuals from the lqzc workspace.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The user question or search phrase"},
                    "top_k": {"type": "integer", "description": "How many hits to return", "default": 3},
                },
                "required": ["query"],
            },
            handler=manual_search.search,
        )
    )

    registry.register(
        ToolDefinition(
            name="load_skill",
            description="Load a skill body on demand. Useful for reusable domain workflows.",
            input_schema={
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": f"Skill name. Available now: {', '.join(skill_loader.list_skill_names()) or '(none)'}",
                    }
                },
                "required": ["skill_name"],
            },
            handler=skill_loader.load,
        )
    )

    return registry
