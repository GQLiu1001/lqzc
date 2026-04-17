"""Approval subagent — high-risk warehouse operations with interrupt_on.

Handles: outbound applications, approval status queries.
Uses interrupt_on for outbound_apply to trigger human-in-the-loop approval.
"""

from __future__ import annotations

from deepagents.middleware.subagents import SubAgent

from app.tools.rag_tools import shared_policy_rag_search, warehouse_rag_search
from app.tools.warehouse_tools import approval_status_query, outbound_apply


def build_approval_subagent() -> SubAgent:
    return SubAgent(
        name="warehouse_approval_subagent",
        description="处理出库申请、审批状态查询和高风险仓储动作。出库申请会触发审批中断。",
        system_prompt="""\
你是仓储审批专家。
只处理出库申请、审批状态、审批流相关问题。
如果是高风险仓储动作，必须通过审批机制。
如参数不完整，应先追问，不要直接提交。

工具使用指引：
1. 提交出库申请 → outbound_apply(warehouse_id, item_id, qty, reason)
   - 必须确认仓库编号、商品 ID、数量三个参数齐全
   - 缺少任何一个都应追问用户
   - 此工具会触发审批中断，等待管理员 approve / reject
2. 查审批状态 → approval_status_query(approval_id)
   - 返回 pending / approved / rejected
3. 解释审批依据、审批规范时，可调用 warehouse_rag_search 或 shared_policy_rag_search

回答格式：
- 审批提交后告知审批单号和当前状态
- 审批查询时用中文状态（待审批/已通过/已拒绝）""",
        tools=[outbound_apply, approval_status_query, warehouse_rag_search, shared_policy_rag_search],
        skills=[
            "/skills/shared/response_format/",
            "/skills/warehouse/outbound_approval/",
        ],
        interrupt_on={
            "outbound_apply": {"allowed_decisions": ["approve", "reject"]},
        },
    )
