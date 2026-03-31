"""Centralized runtime settings for the harness."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


# Load `.env` automatically so the project is easy to run locally.
load_dotenv(override=False)


@dataclass(slots=True)
class Settings:
    """Keep runtime configuration in one place.

    The harness is easiest to study when all important paths and URLs
    are visible and explicit, so this dataclass also computes a few
    derived directories.
    """

    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api")
    )
    ollama_model: str = field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen3:latest")
    )
    ollama_think: bool = field(
        default_factory=lambda: os.getenv("OLLAMA_THINK", "false").lower() == "true"
    )
    ollama_embed_model: str = field(
        default_factory=lambda: os.getenv("OLLAMA_EMBED_MODEL", "qwen3-embedding:8b")
    )
    lqzc_base_url: str = field(
        default_factory=lambda: os.getenv("LQZC_BASE_URL", "http://localhost:8001")
    )
    lqzc_mcp_enabled: bool = field(
        default_factory=lambda: os.getenv("LQZC_MCP_ENABLED", "true").lower() == "true"
    )
    lqzc_mcp_url: str = field(
        default_factory=lambda: os.getenv("LQZC_MCP_URL", "http://localhost:8001/mcp")
    )
    lqzc_customer_token: str = field(
        default_factory=lambda: os.getenv("LQZC_CUSTOMER_TOKEN", "")
    )
    db_path_raw: str = field(
        default_factory=lambda: os.getenv("HARNESS_DB_PATH", "./data/tao_harness.db")
    )
    max_agent_steps: int = field(
        default_factory=lambda: int(os.getenv("MAX_AGENT_STEPS", "8"))
    )
    postgres_host: str = field(
        default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost")
    )
    postgres_port: int = field(
        default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432"))
    )
    postgres_db: str = field(
        default_factory=lambda: os.getenv("POSTGRES_DB", "tao_ai_demo")
    )
    postgres_user: str = field(
        default_factory=lambda: os.getenv("POSTGRES_USER", "postgres")
    )
    postgres_password: str = field(
        default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "123123")
    )
    postgres_dsn: str = field(
        default_factory=lambda: os.getenv("POSTGRES_DSN", "").strip()
    )
    rag_top_k: int = field(
        default_factory=lambda: int(os.getenv("RAG_TOP_K", "4"))
    )
    project_root: Path = field(init=False)
    workspace_root: Path = field(init=False)
    prompts_dir: Path = field(init=False)
    skills_dir: Path = field(init=False)
    data_dir: Path = field(init=False)
    db_path: Path = field(init=False)
    manuals_dir: Path = field(init=False)
    upload_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        self.project_root = Path(__file__).resolve().parents[1]
        # The harness lives at: lqzc/tao-ai/tao-harness
        # The business workspace root is therefore: lqzc/
        self.workspace_root = self.project_root.parents[1]
        self.prompts_dir = self.project_root / "prompts"
        self.skills_dir = self.project_root / "skills"
        self.data_dir = self.project_root / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = (self.project_root / self.db_path_raw).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.manuals_dir = self.workspace_root / "src" / "main" / "resources" / "manuals"
        self.upload_dir = self.workspace_root / "doc"
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        if not self.postgres_dsn:
            self.postgres_dsn = (
                f"host={self.postgres_host} "
                f"port={self.postgres_port} "
                f"dbname={self.postgres_db} "
                f"user={self.postgres_user} "
                f"password={self.postgres_password} "
                "connect_timeout=3"
            )


settings = Settings()
