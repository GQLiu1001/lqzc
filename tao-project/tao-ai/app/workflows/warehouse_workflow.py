"""提供与仓储工作流相关的实现。"""

from __future__ import annotations

from app.agents.warehouse.agent import WarehouseAgent
from app.memory.memory_store import MemoryStore
from app.tools.approval_tools.approval_tool import ApprovalTool
from app.tools.mcp_tools.lqzc_tools import LQZCBusinessTools
from app.tools.rag_tools.retriever_tool import RetrieverTool
from app.workflows.domain_subworkflow import DomainSubWorkflow


class WarehouseWorkflow(DomainSubWorkflow):
    """封装仓储工作流，负责把多个步骤按状态图串联起来执行。"""
    def __init__(
        self,
        *,
        memory: MemoryStore,
        warehouse_agent: WarehouseAgent,
        retriever_tool: RetrieverTool,
        business_tools: LQZCBusinessTools,
        approval_tool: ApprovalTool,
    ) -> None:
        """初始化仓储工作流，把运行时依赖和基础状态准备好。"""
        async def _answer(
            message: str,
            context: str,
            skill_instruction: str,
            response_contract: str,
        ) -> str:
            """作为内部辅助步骤，完成answer相关处理。"""
            return await warehouse_agent.answer(
                message=message,
                context=context,
                skill_instruction=skill_instruction,
                response_contract=response_contract,
            )

        super().__init__(
            workflow_name="warehouse_subgraph",
            memory=memory,
            retriever_tool=retriever_tool,
            business_tools=business_tools,
            approval_tool=approval_tool,
            answer_generator=_answer,
        )
