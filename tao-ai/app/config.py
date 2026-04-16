"""Runtime settings loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # app
    app_name: str = "tao-ai"
    app_env: Literal["dev", "test", "prod"] = "dev"
    app_port: int = 8000
    log_level: str = "INFO"
    enable_request_logging: bool = True

    # ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen3:8b"
    ollama_embed_model: str = "qwen3-embedding:8b"

    # mysql (M1: 仅保留配置,未接入)
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_db: str = "tao_ai_runtime"
    mysql_user: str = "root"
    mysql_password: str = "root"
    mysql_charset: str = "utf8mb4"

    # milvus (M1: 仅保留配置)
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_embedding_dim: int = 4096
    milvus_customer_faq_collection: str = "customer_faq_collection"
    milvus_customer_policy_collection: str = "customer_policy_collection"
    milvus_warehouse_sop_collection: str = "warehouse_sop_collection"

    # mcp
    lqzc_base_url: str = "http://localhost:8001"
    mcp_server_url: str = "http://localhost:8001/mcp"
    mcp_timeout_seconds: int = 20

    # agent runtime
    rag_top_k: int = 4
    max_agent_steps: int = 8
    enable_approval: bool = True
    enable_llm_supervisor_router: bool = True
    llm_supervisor_router_timeout_seconds: int = 12

    # rerank (M3)
    enable_rerank: bool = True
    rerank_expand_factor: int = 3

    # observability
    enable_metrics: bool = True
    metrics_path: str = "/metrics"

    # m1 开关: 是否使用 stub (内存) 替代真实 MySQL / Milvus / MCP
    use_stub_stores: bool = Field(default=True, description="M1: 用内存实现绕过外部依赖")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
