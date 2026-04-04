"""提供与检索器工具相关的实现。"""

from __future__ import annotations

from app.retrieval.retriever_factory import MilvusRetriever


class RetrieverTool:
    """封装检索器工具，对外提供可被工作流调用的工具能力。"""
    def __init__(self, retriever: MilvusRetriever) -> None:
        """初始化检索器工具，把运行时依赖和基础状态准备好。"""
        self.retriever = retriever

    def retrieve(self, *, query: str, domain: str, tenant_id: str | None, top_k: int) -> tuple[str, list[dict]]:
        """检索retrieve相关证据，为回答或决策提供依据。"""
        return self.retriever.search(query=query, domain=domain, tenant_id=tenant_id, top_k=top_k)

