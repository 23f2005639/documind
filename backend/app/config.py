"""Application configuration management"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # =========================
    # App
    # =========================
    app_name: str = "DocuMind API"
    app_version: str = "1.0.0"
    debug: bool = True

    # =========================
    # Supabase
    # =========================
    supabase_url: str = ""
    supabase_key: str = ""

    # =========================
    # Security
    # =========================
    secret_key: str = "super-secret-key"

    # =========================
    # Database
    # =========================
    database_url: str = ""

    # =========================
    # CORS
    # =========================
    cors_origins: str = "*"

    # =========================
    # Logging
    # =========================
    log_level: str = "INFO"
    log_format: str = "console"

    # =========================
    # Embedding
    # =========================
    embedding_dimension: int = 384
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # =========================
    # Vector DB
    # =========================
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "documind-vectors"
    qdrant_local_path: str = "./qdrant_storage"

    # =========================
    # LLM
    # =========================
    openrouter_api_key: str | None = None
    groq_api_key: str | None = None

    ollama_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4:31b-cloud"

    # =========================
    # Notion
    # =========================
    notion_api_key: str | None = None
    notion_database_id: str | None = None

    # =========================
    # GitHub
    # =========================
    github_app_id: str | None = None
    github_private_key: str | None = None
    github_webhook_secret: str | None = None

    # =========================
    # Redis
    # =========================
    redis_url: str = "redis://localhost:6379"
    # =========================
    # AI / Generation
# =========================
    max_tokens: int = 4096
    temperature: float = 0.7

# =========================
# Rate Limiting
# =========================
    rate_limit_per_minute: int = 60

# =========================
# Cache
# =========================
    cache_ttl: int = 3600

# =========================
# Search
# =========================
    top_k_results: int = 5

# =========================
# Chunking
# =========================
    chunk_size: int = 1000
    chunk_overlap: int = 200
    app_env: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


# Global settings instance
settings = Settings()