"""Runtime settings for the refactored Tao AI runtime.

Stack target:
- LangChain + LangGraph
- Milvus
- MySQL
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(override=False)


@dataclass(slots=True)
class Settings:
    """集中管理项目运行配置。

    这个类相当于项目的“总配置表”：
    所有环境变量最终都会被整理到这里，后面各层代码只依赖 `settings`，
    而不是到处直接 `os.getenv(...)`。

    这样做的好处是：
    - 配置来源统一
    - 默认值集中
    - 更容易知道一个功能依赖哪些开关
    """
    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "agent-runtime"))
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "dev"))
    app_port: int = field(default_factory=lambda: int(os.getenv("APP_PORT", "8000")))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    enable_request_logging: bool = field(default_factory=lambda: os.getenv("ENABLE_REQUEST_LOGGING", "true").lower() == "true")
    enable_metrics: bool = field(default_factory=lambda: os.getenv("ENABLE_METRICS", "true").lower() == "true")
    metrics_path: str = field(default_factory=lambda: os.getenv("METRICS_PATH", "/metrics"))
    metrics_collect_interval_seconds: int = field(default_factory=lambda: int(os.getenv("METRICS_COLLECT_INTERVAL_SECONDS", "5")))
    metrics_task_stuck_seconds: int = field(default_factory=lambda: int(os.getenv("METRICS_TASK_STUCK_SECONDS", "120")))
    metrics_task_loop_step_threshold: int = field(default_factory=lambda: int(os.getenv("METRICS_TASK_LOOP_STEP_THRESHOLD", "80")))

    ollama_base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_chat_model: str = field(default_factory=lambda: os.getenv("OLLAMA_CHAT_MODEL", "qwen3:8b"))
    ollama_embed_model: str = field(default_factory=lambda: os.getenv("OLLAMA_EMBED_MODEL", "qwen3-embedding:8b"))

    mysql_host: str = field(default_factory=lambda: os.getenv("MYSQL_HOST", "localhost"))
    mysql_port: int = field(default_factory=lambda: int(os.getenv("MYSQL_PORT", "3306")))
    mysql_db: str = field(default_factory=lambda: os.getenv("MYSQL_DB", "tao_ai_runtime"))
    mysql_user: str = field(default_factory=lambda: os.getenv("MYSQL_USER", "root"))
    mysql_password: str = field(default_factory=lambda: os.getenv("MYSQL_PASSWORD", "root"))
    mysql_charset: str = field(default_factory=lambda: os.getenv("MYSQL_CHARSET", "utf8mb4"))

    milvus_host: str = field(default_factory=lambda: os.getenv("MILVUS_HOST", "localhost"))
    milvus_port: int = field(default_factory=lambda: int(os.getenv("MILVUS_PORT", "19530")))
    milvus_db: str = field(default_factory=lambda: os.getenv("MILVUS_DB", "default"))
    milvus_embedding_dim: int = field(default_factory=lambda: int(os.getenv("MILVUS_EMBEDDING_DIM", "4096")))

    mcp_server_url: str = field(default_factory=lambda: os.getenv("MCP_SERVER_URL", "http://localhost:8001/mcp"))
    mcp_protocol_version: str = field(default_factory=lambda: os.getenv("MCP_PROTOCOL_VERSION", "2025-06-18"))
    mcp_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("MCP_TIMEOUT_SECONDS", "20")))
    lqzc_base_url: str = field(default_factory=lambda: os.getenv("LQZC_BASE_URL", "http://localhost:8001"))
    lqzc_customer_token: str = field(default_factory=lambda: os.getenv("LQZC_CUSTOMER_TOKEN", ""))
    lqzc_admin_token: str = field(default_factory=lambda: os.getenv("LQZC_ADMIN_TOKEN", ""))

    rag_top_k: int = field(default_factory=lambda: int(os.getenv("RAG_TOP_K", "4")))
    max_agent_steps: int = field(default_factory=lambda: int(os.getenv("MAX_AGENT_STEPS", "8")))

    enable_approval: bool = field(default_factory=lambda: os.getenv("ENABLE_APPROVAL", "true").lower() == "true")
    approval_admin_token: str = field(default_factory=lambda: os.getenv("APPROVAL_ADMIN_TOKEN", ""))
    enable_trace: bool = field(default_factory=lambda: os.getenv("ENABLE_TRACE", "true").lower() == "true")
    enable_eval: bool = field(default_factory=lambda: os.getenv("ENABLE_EVAL", "true").lower() == "true")
    enable_llm_skill_router: bool = field(default_factory=lambda: os.getenv("ENABLE_LLM_SKILL_ROUTER", "true").lower() == "true")
    llm_skill_router_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("LLM_SKILL_ROUTER_TIMEOUT_SECONDS", "12")))
    llm_skill_router_min_rule_score: int = field(default_factory=lambda: int(os.getenv("LLM_SKILL_ROUTER_MIN_RULE_SCORE", "16")))

    customer_faq_collection: str = field(default_factory=lambda: os.getenv("MILVUS_CUSTOMER_FAQ_COLLECTION", "customer_faq_collection"))
    customer_policy_collection: str = field(default_factory=lambda: os.getenv("MILVUS_CUSTOMER_POLICY_COLLECTION", "customer_policy_collection"))
    warehouse_sop_collection: str = field(default_factory=lambda: os.getenv("MILVUS_WAREHOUSE_SOP_COLLECTION", "warehouse_sop_collection"))
    business_rules_collection: str = field(default_factory=lambda: os.getenv("MILVUS_BUSINESS_RULES_COLLECTION", "business_rules_collection"))
    historical_case_collection: str = field(default_factory=lambda: os.getenv("MILVUS_HISTORICAL_CASE_COLLECTION", "historical_case_collection"))

    project_root: Path = field(init=False)
    prompts_dir: Path = field(init=False)
    skills_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        """补充由路径推导出来的配置。

        前面的字段大多来自环境变量；
        这里则根据当前文件位置，自动推导出项目根目录、prompt 目录、skill 目录。
        """
        self.project_root = Path(__file__).resolve().parents[1]
        self.prompts_dir = self.project_root / "prompts"
        self.skills_dir = self.project_root / "skills"

    @property
    def mysql_dsn(self) -> dict[str, object]:
        """把 MySQL 连接配置整理成可直接传给客户端的参数字典。"""
        return {
            "host": self.mysql_host,
            "port": self.mysql_port,
            "user": self.mysql_user,
            "password": self.mysql_password,
            "database": self.mysql_db,
            "charset": self.mysql_charset,
            "autocommit": True,
            "cursorclass": None,
        }


settings = Settings()
