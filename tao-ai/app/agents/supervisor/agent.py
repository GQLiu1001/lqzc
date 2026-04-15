"""Supervisor routing agent."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import logging
import re
from typing import Any, Mapping

from app.config import settings
from app.models.chat import ChatService


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RouteDecision:
    """Supervisor routing result."""

    agent: str
    risk_level: str
    requires_approval: bool
    retrieval_domain: str
    route_reason: str
    route_source: str
    route_confidence: float | None = None


class SupervisorAgent:
    """Routes a task to a real business domain.

    This class does not implement a fake Skill registry. It asks the model to
    choose between the runtime's real subgraphs: customer service or warehouse.
    """

    def __init__(self, *, chat_service: ChatService | None = None) -> None:
        self.chat_service = chat_service

    async def route(self, message: str, *, context: Mapping[str, Any] | None = None) -> RouteDecision:
        if not settings.enable_llm_supervisor_router:
            raise RuntimeError("LLM supervisor router is disabled")
        if self.chat_service is None:
            raise RuntimeError("Supervisor routing requires a chat service")

        agent, risk_level, requires_approval, confidence, reason = await self._route_with_llm(
            message=message,
            context=context or {},
        )
        if agent not in {"customer_service", "warehouse"}:
            raise RuntimeError(f"Supervisor returned unsupported agent: {agent}")

        risk = risk_level if risk_level in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} else "LOW"
        return RouteDecision(
            agent=agent,
            risk_level=risk,
            requires_approval=bool(requires_approval),
            retrieval_domain=agent,
            route_reason=reason,
            route_source="llm",
            route_confidence=confidence,
        )

    async def _route_with_llm(
        self,
        *,
        message: str,
        context: Mapping[str, Any],
    ) -> tuple[str, str, bool, float | None, str]:
        prompt = (
            "你是业务域路由器，只能在 customer_service 和 warehouse 之间选择。\n"
            "customer_service: 订单、物流、售后、退款、客服回复。\n"
            "warehouse: 库存、仓储、补货、锁库、出入库、质检 SOP。\n"
            "如果请求涉及退款、赔付、取消订单、库存变更、锁库、冻结、释放、扣减，"
            "requires_approval 必须为 true，risk_level 至少为 HIGH。\n"
            "只允许输出 JSON："
            '{"agent":"customer_service|warehouse","risk_level":"LOW|MEDIUM|HIGH|CRITICAL",'
            '"requires_approval":true|false,"confidence":0.0-1.0,"reason":"<short reason>"}。'
        )
        user_text = (
            f"用户问题：{message}\n"
            f"上下文：{json.dumps(dict(context), ensure_ascii=False)}"
        )

        try:
            raw = await asyncio.wait_for(
                self.chat_service.generate(
                    system_prompt=prompt,
                    user_message=user_text,
                    context="",
                ),
                timeout=settings.llm_supervisor_router_timeout_seconds,
            )
        except Exception as exc:
            raise RuntimeError(f"Supervisor routing failed: {exc}") from exc

        parsed = self._try_parse_router_json(raw)
        if parsed is None:
            raise RuntimeError("Supervisor routing failed: invalid JSON")

        agent = str(parsed.get("agent") or "").strip()
        risk_level = str(parsed.get("risk_level") or "LOW").strip().upper()
        requires_approval = bool(parsed.get("requires_approval"))
        confidence = self._safe_confidence(parsed.get("confidence"))
        reason = str(parsed.get("reason") or "domain selected by supervisor")
        logger.info(
            "supervisor.route.llm agent=%s risk=%s approval=%s confidence=%s reason=%s",
            agent,
            risk_level,
            requires_approval,
            confidence,
            reason,
        )
        return agent, risk_level, requires_approval, confidence, reason

    @staticmethod
    def _safe_confidence(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _try_parse_router_json(raw: str) -> dict[str, Any] | None:
        content = raw.strip()
        if not content:
            return None
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)
            content = re.sub(r"\s*```$", "", content).strip()
        try:
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            pass
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if match is None:
            return None
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
