from __future__ import annotations

from app.retrieval.retriever_factory import MilvusRetriever


class RetrieverTool:
    def __init__(self, retriever: MilvusRetriever) -> None:
        self.retriever = retriever

    def retrieve(self, *, query: str, domain: str, tenant_id: str | None, top_k: int) -> tuple[str, list[dict]]:
        return self.retriever.search(query=query, domain=domain, tenant_id=tenant_id, top_k=top_k)

