from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import settings

TAO_AI_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = TAO_AI_ROOT.parent
CACHE_ROOT = TAO_AI_ROOT / settings.rag_cache_dir
CHUNK_CACHE_PATH = CACHE_ROOT / "chunks.json"

SUPPORTED_DOC_SUFFIXES = {".md", ".markdown", ".txt"}
DEFAULT_TOP_K = settings.rag_default_top_k
DEFAULT_RECALL_K = settings.rag_recall_k
DEFAULT_CHUNK_SIZE = settings.rag_chunk_size
DEFAULT_CHUNK_OVERLAP = settings.rag_chunk_overlap
MIN_RETRIEVAL_SCORE = settings.rag_min_score
MIN_RERANK_SCORE = settings.rag_min_rerank_score

PUBLIC_ACCESS = "public"
CUSTOMER_ACCESS = "customer"
STAFF_ACCESS = "staff"

SCENE_HINTS: dict[str, tuple[str, ...]] = {
    "general": (),
    "product_consult": ("商品", "参数", "规格", "型号", "适用场景"),
    "aftersale_policy": ("售后", "退换货", "退款", "发票", "保修"),
    "order_query": ("订单", "支付", "收货", "物流"),
    "inventory_query": ("库存", "入库", "出库", "调拨", "仓库"),
    "outbound_approval": ("审批", "出库", "放行", "待审批"),
    "shared_policy": ("平台规则", "统一政策", "通用说明"),
}


@dataclass(frozen=True, slots=True)
class KnowledgeSource:
    name: str
    root: Path
    domain: str
    scene: str | None = None
    source_type: str = "manual"
    access_level: str = PUBLIC_ACCESS
    role_allowlist: tuple[str, ...] = ()
    warehouse_scope: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


def default_knowledge_sources() -> list[KnowledgeSource]:
    return [
        KnowledgeSource(
            name="mall_manuals",
            root=PROJECT_ROOT / "src" / "main" / "resources" / "manuals",
            domain="mall",
            scene="aftersale_policy",
            source_type="manual",
            access_level=CUSTOMER_ACCESS,
        ),
        KnowledgeSource(
            name="mall_skills",
            root=TAO_AI_ROOT / "skills" / "mall",
            domain="mall",
            source_type="skill",
            access_level=CUSTOMER_ACCESS,
        ),
        KnowledgeSource(
            name="warehouse_skills",
            root=TAO_AI_ROOT / "skills" / "warehouse",
            domain="warehouse",
            source_type="skill",
            access_level=STAFF_ACCESS,
            role_allowlist=("staff", "warehouse_manager", "admin"),
        ),
        KnowledgeSource(
            name="shared_skills",
            root=TAO_AI_ROOT / "skills" / "shared",
            domain="shared",
            source_type="skill",
            access_level=PUBLIC_ACCESS,
        ),
        KnowledgeSource(
            name="knowledge_mall",
            root=TAO_AI_ROOT / "knowledge" / "mall",
            domain="mall",
            source_type="knowledge_base",
            access_level=CUSTOMER_ACCESS,
        ),
        KnowledgeSource(
            name="knowledge_warehouse",
            root=TAO_AI_ROOT / "knowledge" / "warehouse",
            domain="warehouse",
            source_type="knowledge_base",
            access_level=STAFF_ACCESS,
            role_allowlist=("staff", "warehouse_manager", "admin"),
        ),
        KnowledgeSource(
            name="knowledge_shared",
            root=TAO_AI_ROOT / "knowledge" / "shared",
            domain="shared",
            source_type="knowledge_base",
            access_level=PUBLIC_ACCESS,
        ),
    ]
