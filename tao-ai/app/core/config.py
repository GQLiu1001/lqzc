from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "tao-ai-agent"
    app_env: str = "dev"
    app_port: int = 8000

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen3:8b"
    ollama_embed_model: str = "qwen3-embedding:8b"

    postgres_dsn: str = (
        "postgresql://postgres:postgres@127.0.0.1:5432/agent_db?sslmode=disable"
    )

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_db: str = "default"

    mcp_server_url: str = "http://localhost:8001/mcp"
    mcp_timeout_seconds: int = 20

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
