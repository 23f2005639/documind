"""Application configuration management"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "DocuMind"
    app_env: str = "development"
    debug: bool = True
    secret_key: str
    
    # Database (Supabase)
    supabase_url: str
    supabase_key: str
    database_url: str
    
    # Vector Store (Qdrant Cloud)
    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection_name: str = "documind-vectors"
    
    # LLM (Ollama Cloud — https://ollama.com)
    ollama_api_key: str
    ollama_base_url: str = "https://ollama.com"
    ollama_model: str = "gpt-oss:20b"
    ollama_max_tokens: int = 2000
    
    # Notion
    notion_api_key: str
    notion_database_id: str
    
    # GitHub
    github_app_id: str
    github_private_key: str
    github_webhook_secret: str
    
    # Embedding
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    notion_rate_limit: int = 3
    max_requests_per_day: int = 14400  # Ollama Cloud free tier
    
    # Caching (Redis)
    redis_url: str = "redis://localhost:6379"
    enable_cache: bool = True
    cache_ttl_hours: int = 24
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Feature Flags
    enable_staleness_detection: bool = True
    enable_quality_scoring: bool = True
    enable_coverage_metrics: bool = True
    
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), case_sensitive=False)


# Global settings instance
settings = Settings()

# Made with Bob
