"""提供与DEPS相关的实现。"""

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
    """运行时依赖容器。

    这个类可以理解成“应用启动时的一次性装配中心”：
    它负责把模型、记忆层、检索器、工具、工作流这些对象组装起来，
    让 API 层不需要在每次请求里重复手动创建一整套依赖。
    """
    def __init__(self) -> None:
        """把整套运行时对象串起来。

        这里的组装顺序很值得理解：
        1. 先创建模型工厂
        2. 再拿到聊天模型和向量模型
        3. 再创建记忆层、检索层、工具层
        4. 最后把这些依赖全部注入总控工作流

        所以这里本质上是在做“依赖注入”。
        """
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
    """返回全局单例运行时容器。

    `lru_cache(maxsize=1)` 的意思是：进程生命周期内只创建一份容器实例。
    这样可以避免每次请求都重复初始化模型客户端、数据库封装、检索器等重对象。
    """
    return RuntimeContainer()
