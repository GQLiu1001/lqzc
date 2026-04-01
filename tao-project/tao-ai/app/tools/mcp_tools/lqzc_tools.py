from __future__ import annotations

from dataclasses import dataclass
import logging
import re
import time
import uuid
from typing import Any

import httpx

from app.config import settings
from app.observability.metrics import metrics
from app.tools.mcp_tools.client import LQZCMcpClient


# Avoid \b because Chinese characters are considered word chars in Unicode regex,
# which makes tokens like "查下A8001库存" fail to match.
_MODEL_TOKEN = re.compile(r"(?<![A-Za-z0-9-])([A-Za-z]{1,6}[0-9]{2,}[A-Za-z0-9-]*)(?![A-Za-z0-9-])")
_INVENTORY_HINTS = ("库存", "有货", "现货", "stock", "in stock")
_ORDER_TOKEN = re.compile(r"(?<![A-Za-z0-9-])([A-Za-z]{0,4}[0-9]{6,20}[A-Za-z0-9-]*)(?![A-Za-z0-9-])")
_ORDER_HINTS = ("订单", "物流", "发货", "催单", "签收")
_ADJUSTMENT_QUANTITY = re.compile(r"(?:锁库|冻结|扣减|减少|下调|补货|增加|上调|释放|解冻|调整)\D{0,8}(-?\d{1,6})")
_DECREASE_HINTS = ("锁库", "冻结", "扣减", "减少", "下调")
_INCREASE_HINTS = ("补货", "增加", "上调", "释放", "解冻")

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ToolExecution:
    tool_name: str
    status: str
    arguments: dict[str, Any]
    result: Any

    def as_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "status": self.status,
            "arguments": self.arguments,
            "result": self.result,
        }


class LQZCBusinessTools:
    def __init__(self) -> None:
        self.mcp_client = LQZCMcpClient(settings.mcp_server_url)

    async def get_order_detail(self, order_no: str) -> dict[str, Any]:
        started_at = time.perf_counter()
        if not settings.lqzc_customer_token:
            elapsed = time.perf_counter() - started_at
            metrics.observe_tool_call(
                tool_name="get_order_detail",
                status="FAILED_CONFIG",
                duration_seconds=elapsed,
            )
            return {
                "code": 401,
                "message": "LQZC_CUSTOMER_TOKEN not configured",
                "data": None,
            }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(
                    f"{settings.lqzc_base_url}/mall/order/detail/{order_no}",
                    headers={"X-Customer-Token": settings.lqzc_customer_token},
                )
                response.raise_for_status()
                data = response.json()
                elapsed = time.perf_counter() - started_at
                metrics.observe_tool_call(
                    tool_name="get_order_detail",
                    status="SUCCESS",
                    duration_seconds=elapsed,
                )
                return data
        except Exception:
            elapsed = time.perf_counter() - started_at
            metrics.observe_tool_call(
                tool_name="get_order_detail",
                status="FAILED",
                duration_seconds=elapsed,
            )
            raise

    async def get_inventory_by_model(self, model: str) -> dict[str, Any]:
        data = await self.mcp_client.call_tool("getInventoryByModel", {"model": model.upper()})
        return {"code": 200, "message": "success", "data": data}

    async def search_inventory(self, current: int = 1, size: int = 10, category: str | None = None, surface: str | None = None) -> dict[str, Any]:
        payload = {"current": current, "size": size}
        if category:
            payload["category"] = category
        if surface:
            payload["surface"] = surface
        data = await self.mcp_client.call_tool("searchInventory", payload)
        return {"code": 200, "message": "success", "data": data}

    def execute_planned_action_sync(
        self,
        *,
        source_tool: str,
        planned_action: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        if source_tool == "submit_refund_for_approval":
            return self._execute_refund_action_sync(planned_action=planned_action, idempotency_key=idempotency_key)
        if source_tool == "submit_inventory_adjustment_for_approval":
            return self._execute_inventory_adjustment_sync(
                planned_action=planned_action,
                idempotency_key=idempotency_key,
            )
        return {
            "code": 422,
            "message": f"unsupported planned action source tool: {source_tool}",
            "data": None,
        }

    def _execute_refund_action_sync(self, *, planned_action: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        endpoint = str(planned_action.get("endpoint") or "").strip()
        if not endpoint:
            return {"code": 422, "message": "missing endpoint in planned_action", "data": None}
        if not settings.lqzc_customer_token:
            return {"code": 401, "message": "LQZC_CUSTOMER_TOKEN not configured", "data": None}
        method = str(planned_action.get("method") or "POST").upper()
        params = planned_action.get("params") if isinstance(planned_action.get("params"), dict) else None
        return self._request_lqzc_api_sync(
            method=method,
            endpoint=endpoint,
            params=params,
            json_body=None,
            headers={
                "X-Customer-Token": settings.lqzc_customer_token,
                "X-Idempotency-Key": idempotency_key,
            },
            tool_name="execute_refund_action",
        )

    def _execute_inventory_adjustment_sync(self, *, planned_action: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        endpoint = str(planned_action.get("endpoint") or "").strip()
        if not endpoint:
            return {"code": 422, "message": "missing endpoint in planned_action", "data": None}
        if not settings.lqzc_admin_token:
            return {"code": 401, "message": "LQZC_ADMIN_TOKEN not configured", "data": None}
        method = str(planned_action.get("method") or "PUT").upper()
        body = planned_action.get("body") if isinstance(planned_action.get("body"), dict) else None
        if body is None:
            return {"code": 422, "message": "missing body in planned_action", "data": None}
        return self._request_lqzc_api_sync(
            method=method,
            endpoint=endpoint,
            params=None,
            json_body=body,
            headers={
                "Authorization": f"Bearer {settings.lqzc_admin_token}",
                "X-Idempotency-Key": idempotency_key,
            },
            tool_name="execute_inventory_adjustment_action",
        )

    def _request_lqzc_api_sync(
        self,
        *,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None,
        json_body: dict[str, Any] | None,
        headers: dict[str, str],
        tool_name: str,
    ) -> dict[str, Any]:
        started_at = time.perf_counter()
        url = endpoint if endpoint.startswith("http") else f"{settings.lqzc_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.request(
                    method,
                    url,
                    params=params,
                    json=json_body,
                    headers=headers,
                )
            elapsed = time.perf_counter() - started_at
            raw_data: Any
            try:
                raw_data = response.json()
            except Exception:
                raw_data = response.text

            if response.status_code >= 400:
                metrics.observe_tool_call(tool_name=tool_name, status="FAILED", duration_seconds=elapsed)
                return {
                    "code": response.status_code,
                    "message": f"{method} {endpoint} failed",
                    "data": raw_data,
                }

            metrics.observe_tool_call(tool_name=tool_name, status="SUCCESS", duration_seconds=elapsed)
            if isinstance(raw_data, dict) and "code" in raw_data and "message" in raw_data:
                return raw_data
            return {"code": 200, "message": "success", "data": raw_data}
        except Exception as exc:
            metrics.observe_tool_call(
                tool_name=tool_name,
                status="FAILED",
                duration_seconds=time.perf_counter() - started_at,
            )
            logger.exception("tool.execute.action.failed tool=%s endpoint=%s", tool_name, endpoint)
            return {"code": 500, "message": f"{tool_name} failed: {exc}", "data": None}

    async def run_by_skill(
        self,
        *,
        skill_name: str,
        message: str,
        tool_hints: tuple[str, ...] = (),
    ) -> list[dict[str, Any]]:
        logger.info(
            "tool.dispatch.start skill=%s tool_hints=%s",
            skill_name,
            ",".join(tool_hints) if tool_hints else "",
        )
        hint_queue = self._build_hint_queue(skill_name=skill_name, message=message, tool_hints=tool_hints)

        results: list[ToolExecution] = []
        for hint in hint_queue:
            execution = await self._execute_hint(hint=hint, message=message)
            results.append(execution)
            logger.info(
                "tool.dispatch.item skill=%s tool=%s status=%s",
                skill_name,
                execution.tool_name,
                execution.status,
            )

        logger.info(
            "tool.dispatch.end skill=%s tool_count=%s tools=%s",
            skill_name,
            len(results),
            ",".join(f"{item.tool_name}:{item.status}" for item in results),
        )
        return [item.as_dict() for item in results]

    def _build_hint_queue(self, *, skill_name: str, message: str, tool_hints: tuple[str, ...]) -> list[str]:
        ordered_hints: list[str] = []
        seen: set[str] = set()
        for raw in tool_hints:
            hint = raw.strip()
            if not hint or hint in seen:
                continue
            seen.add(hint)
            ordered_hints.append(hint)

        if ordered_hints:
            return ordered_hints

        lowered = message.lower()
        auto_hints: list[str] = []
        model = self._extract_model(message)
        order_no = self._extract_order_no(message)
        if model is not None or any(token in lowered for token in _INVENTORY_HINTS):
            auto_hints.append("get_inventory_by_model" if model else "search_inventory")
        if order_no is not None or any(token in lowered for token in _ORDER_HINTS):
            auto_hints.append("get_order_detail")
        if not auto_hints:
            if skill_name in {"inventory_exception_skill", "replenishment_suggestion_skill"}:
                auto_hints.append("search_inventory")
            elif skill_name in {"order_status_explain_skill", "after_sale_intake_skill"}:
                auto_hints.append("get_order_detail")
        return auto_hints

    async def _execute_hint(self, *, hint: str, message: str) -> ToolExecution:
        handlers = {
            "get_order_detail": self._run_get_order_detail,
            "get_inventory_by_model": self._run_get_inventory_by_model,
            "search_inventory": self._run_search_inventory,
            "create_after_sale_ticket": self._run_create_after_sale_ticket,
            "submit_refund_for_approval": self._run_submit_refund_for_approval,
            "submit_inventory_adjustment_for_approval": self._run_submit_inventory_adjustment_for_approval,
        }
        handler = handlers.get(hint)
        if handler is None:
            return ToolExecution(
                tool_name=hint,
                status="SKIPPED_UNSUPPORTED",
                arguments={"message": message},
                result={
                    "code": 501,
                    "message": f"Tool `{hint}` not implemented in runtime",
                    "data": None,
                },
            )
        return await handler(message)

    async def _run_get_order_detail(self, message: str) -> ToolExecution:
        order_no = self._extract_order_no(message)
        args = {"message": message, "order_no": order_no}
        if order_no is None:
            return ToolExecution(
                tool_name="get_order_detail",
                status="FAILED_INPUT",
                arguments=args,
                result={"code": 422, "message": "order_no not found in message", "data": None},
            )
        try:
            data = await self.get_order_detail(order_no)
            if data.get("code") == 401:
                return ToolExecution("get_order_detail", "FAILED_CONFIG", args, data)
            if int(data.get("code", 200)) >= 400:
                return ToolExecution("get_order_detail", "FAILED", args, data)
            return ToolExecution("get_order_detail", "SUCCESS", args, data)
        except Exception as exc:
            return ToolExecution(
                tool_name="get_order_detail",
                status="FAILED",
                arguments=args,
                result={"code": 500, "message": f"get_order_detail failed: {exc}", "data": None},
            )

    async def _run_get_inventory_by_model(self, message: str) -> ToolExecution:
        model = self._extract_model(message)
        args = {"message": message, "model": model}
        if model is None:
            return ToolExecution(
                tool_name="get_inventory_by_model",
                status="FAILED_INPUT",
                arguments=args,
                result={"code": 422, "message": "model not found in message", "data": None},
            )
        try:
            data = await self.get_inventory_by_model(model)
            return ToolExecution("get_inventory_by_model", "SUCCESS", args, data)
        except Exception as exc:
            return ToolExecution(
                tool_name="get_inventory_by_model",
                status="FAILED",
                arguments=args,
                result={"code": 500, "message": f"get_inventory_by_model failed: {exc}", "data": None},
            )

    async def _run_search_inventory(self, message: str) -> ToolExecution:
        args = {"message": message, "current": 1, "size": 10}
        try:
            data = await self.search_inventory(current=1, size=10)
            return ToolExecution("search_inventory", "SUCCESS", args, data)
        except Exception as exc:
            return ToolExecution(
                tool_name="search_inventory",
                status="FAILED",
                arguments=args,
                result={"code": 500, "message": f"search_inventory failed: {exc}", "data": None},
            )

    async def _run_create_after_sale_ticket(self, message: str) -> ToolExecution:
        started_at = time.perf_counter()
        order_no = self._extract_order_no(message)
        args = {"message": message, "order_no": order_no}
        if order_no is None:
            status = "FAILED_INPUT"
            metrics.observe_tool_call(
                tool_name="create_after_sale_ticket",
                status=status,
                duration_seconds=time.perf_counter() - started_at,
            )
            return ToolExecution(
                tool_name="create_after_sale_ticket",
                status=status,
                arguments=args,
                result={"code": 422, "message": "order_no not found in message", "data": None},
            )

        ticket_id = f"afs_{uuid.uuid4().hex[:12]}"
        result = {
            "code": 200,
            "message": "after-sale ticket draft created",
            "data": {
                "ticket_id": ticket_id,
                "order_no": order_no,
                "status": "DRAFT",
                "next_action": "manual_submit_required",
                "planned_endpoint": None,
                "reason": "backend after-sale API not available",
            },
        }
        status = "SUCCESS_DRAFT"
        metrics.observe_tool_call(
            tool_name="create_after_sale_ticket",
            status=status,
            duration_seconds=time.perf_counter() - started_at,
        )
        return ToolExecution("create_after_sale_ticket", status, args, result)

    async def _run_submit_refund_for_approval(self, message: str) -> ToolExecution:
        started_at = time.perf_counter()
        order_no = self._extract_order_no(message)
        args = {"message": message, "order_no": order_no}
        if order_no is None:
            status = "FAILED_INPUT"
            metrics.observe_tool_call(
                tool_name="submit_refund_for_approval",
                status=status,
                duration_seconds=time.perf_counter() - started_at,
            )
            return ToolExecution(
                tool_name="submit_refund_for_approval",
                status=status,
                arguments=args,
                result={"code": 422, "message": "order_no not found in message", "data": None},
            )

        request_id = f"refund_{uuid.uuid4().hex[:12]}"
        result = {
            "code": 200,
            "message": "refund approval request drafted",
            "data": {
                "request_id": request_id,
                "order_no": order_no,
                "requires_approval": True,
                "planned_action": {
                    "method": "POST",
                    "endpoint": f"/mall/order/cancel/{order_no}",
                    "params": {"reason": "customer_refund_request"},
                },
                "status": "PENDING_APPROVAL",
            },
        }
        status = "SUCCESS_DRAFT"
        metrics.observe_tool_call(
            tool_name="submit_refund_for_approval",
            status=status,
            duration_seconds=time.perf_counter() - started_at,
        )
        return ToolExecution("submit_refund_for_approval", status, args, result)

    async def _run_submit_inventory_adjustment_for_approval(self, message: str) -> ToolExecution:
        started_at = time.perf_counter()
        model = self._extract_model(message)
        quantity_delta = self._extract_adjustment_delta(message)
        args = {"message": message, "model": model, "quantity_delta": quantity_delta}

        if model is None:
            status = "FAILED_INPUT"
            metrics.observe_tool_call(
                tool_name="submit_inventory_adjustment_for_approval",
                status=status,
                duration_seconds=time.perf_counter() - started_at,
            )
            return ToolExecution(
                tool_name="submit_inventory_adjustment_for_approval",
                status=status,
                arguments=args,
                result={"code": 422, "message": "inventory model not found in message", "data": None},
            )
        if quantity_delta is None or quantity_delta == 0:
            status = "FAILED_INPUT"
            metrics.observe_tool_call(
                tool_name="submit_inventory_adjustment_for_approval",
                status=status,
                duration_seconds=time.perf_counter() - started_at,
            )
            return ToolExecution(
                tool_name="submit_inventory_adjustment_for_approval",
                status=status,
                arguments=args,
                result={"code": 422, "message": "adjustment quantity not found in message", "data": None},
            )

        snapshot: dict[str, Any] | None = None
        snapshot_error: str | None = None
        try:
            inventory_data = await self.get_inventory_by_model(model)
            if inventory_data.get("code") == 200 and isinstance(inventory_data.get("data"), dict):
                snapshot = inventory_data["data"]
        except Exception as exc:
            snapshot_error = str(exc)

        current_total = None
        if snapshot is not None:
            try:
                current_total = int(snapshot.get("totalAmount"))
            except Exception:
                current_total = None
        proposed_total = (current_total + quantity_delta) if current_total is not None else None

        payload: dict[str, Any] | None = None
        if snapshot is not None:
            payload = {
                "id": snapshot.get("id"),
                "model": snapshot.get("model"),
                "manufacturer": snapshot.get("manufacturer"),
                "specification": snapshot.get("specification"),
                "surface": snapshot.get("surface"),
                "category": snapshot.get("category"),
                "warehouseNum": snapshot.get("warehouseCode"),
                "totalAmount": proposed_total,
                "unitPerBox": snapshot.get("unitPerBox"),
                "sellingPrice": snapshot.get("sellingPrice"),
                "remark": (
                    f"AI draft adjustment, delta={quantity_delta}, requires approval before execution"
                ),
            }

        request_id = f"invadj_{uuid.uuid4().hex[:12]}"
        result = {
            "code": 200,
            "message": "inventory adjustment approval request drafted",
            "data": {
                "request_id": request_id,
                "model": model,
                "quantity_delta": quantity_delta,
                "current_total": current_total,
                "proposed_total": proposed_total,
                "requires_approval": True,
                "planned_action": {
                    "method": "PUT",
                    "endpoint": "/inventory/items-change",
                    "body": payload,
                },
                "inventory_snapshot_error": snapshot_error,
                "status": "PENDING_APPROVAL",
            },
        }
        status = "SUCCESS_DRAFT"
        metrics.observe_tool_call(
            tool_name="submit_inventory_adjustment_for_approval",
            status=status,
            duration_seconds=time.perf_counter() - started_at,
        )
        return ToolExecution("submit_inventory_adjustment_for_approval", status, args, result)

    @staticmethod
    def _extract_model(message: str) -> str | None:
        match = _MODEL_TOKEN.search(message)
        if match is None:
            return None
        return match.group(1).upper()

    @staticmethod
    def _extract_order_no(message: str) -> str | None:
        match = _ORDER_TOKEN.search(message)
        if match is None:
            return None
        return match.group(1)

    @staticmethod
    def _extract_adjustment_delta(message: str) -> int | None:
        match = _ADJUSTMENT_QUANTITY.search(message)
        if match is None:
            return None
        try:
            quantity = int(match.group(1))
        except ValueError:
            return None
        lowered = message.lower()
        if any(token in lowered for token in _DECREASE_HINTS):
            return -abs(quantity)
        if any(token in lowered for token in _INCREASE_HINTS):
            return abs(quantity)
        return quantity
