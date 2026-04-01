from __future__ import annotations

from functools import lru_cache

from app.agents.customer_service.agent import CustomerServiceAgent
from app.agents.supervisor.agent import SupervisorAgent
from app.agents.warehouse.agent import WarehouseAgent
from app.eval.runner import EvalRunner
from app.memory.memory_store import MemoryStore
from app.models.factory import ModelFactory
from app.retrieval.milvus_client import MilvusClient
from app.retrieval.retriever_factory import MilvusRetriever
from app.skills.registry import SkillRegistry
from app.tools.approval_tools.approval_tool import ApprovalTool
from app.tools.mcp_tools.lqzc_tools import LQZCBusinessTools
from app.tools.rag_tools.retriever_tool import RetrieverTool
from app.workflows.supervisor_workflow import SupervisorWorkflow


class RuntimeContainer:
    def __init__(self) -> None:
        model_factory = ModelFactory()
        chat_service = model_factory.create_chat_service()
        memory = MemoryStore()
        retriever = MilvusRetriever(
            embedding_service=model_factory.create_embedding_service(),
            milvus_client=MilvusClient(),
        )
        self.workflow = SupervisorWorkflow(
            memory=memory,
            supervisor_agent=SupervisorAgent(
                skill_registry=SkillRegistry(),
                chat_service=chat_service,
            ),
            customer_agent=CustomerServiceAgent(chat_service),
            warehouse_agent=WarehouseAgent(chat_service),
            retriever_tool=RetrieverTool(retriever),
            business_tools=LQZCBusinessTools(),
            approval_tool=ApprovalTool(memory.mysql),
        )
        self.eval_runner = EvalRunner(workflow=self.workflow, mysql_store=memory.mysql)


@lru_cache(maxsize=1)
def get_runtime_container() -> RuntimeContainer:
    return RuntimeContainer()
