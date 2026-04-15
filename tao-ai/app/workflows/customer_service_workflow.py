"""提供与客服服务工作流相关的实现。"""

from __future__ import annotations

from app.agents.customer_service.agent import CustomerServiceAgent
from app.memory.memory_store import MemoryStore
from app.tools.approval_tools.approval_tool import ApprovalTool
from app.tools.mcp_tools.lqzc_tools import LQZCBusinessTools
from app.tools.rag_tools.retriever_tool import RetrieverTool
from app.workflows.domain_subworkflow import DomainSubWorkflow


class CustomerServiceWorkflow(DomainSubWorkflow):
    """封装客服服务工作流，负责把多个步骤按状态图串联起来执行。"""
    def __init__(
        self,
        *,
        memory: MemoryStore,
        customer_agent: CustomerServiceAgent,
        retriever_tool: RetrieverTool,
        business_tools: LQZCBusinessTools,
        approval_tool: ApprovalTool,
    ) -> None:
        """初始化客服服务工作流，把运行时依赖和基础状态准备好。"""
        async def _answer(
            message: str,
            context: str,
        ) -> str:
            """作为内部辅助步骤，完成answer相关处理。"""
            return await customer_agent.answer(
                message=message,
                context=context,
            )

        super().__init__(
            workflow_name="customer_service_subgraph",
            memory=memory,
            retriever_tool=retriever_tool,
            business_tools=business_tools,
            approval_tool=approval_tool,
            answer_generator=_answer,
        )
