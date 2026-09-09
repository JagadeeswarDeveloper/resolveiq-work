"""Core configuration for ResolveIQ backend."""

from pathlib import Path

from pydantic_settings import BaseSettings
from typing import Optional


LOCAL_DATABASE_URL = f"sqlite:///{(Path(__file__).resolve().parents[2] / 'resolveiq_local_test.db').as_posix()}"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "ResolveIQ"
    environment: str = "development"
    debug: bool = True
    secret_key: str = "dev-secret-key-change-in-production"
    log_level: str = "INFO"

    # Database
    database_url: str = LOCAL_DATABASE_URL
    sqlalchemy_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # CORS
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # LLM Configuration
    llm_provider: str = "ollama"  # ollama, openai, or fallback
    llm_model: str = "neural-chat"  # Ollama model to use
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    
    # AI Mode (live or demo)
    ai_mode: str = "live"  # live uses configured provider, demo uses fallback

    # Embeddings
    embedding_provider: str = "ollama"  # ollama, openai, or fallback
    embedding_model: str = "nomic-embed-text"  # Ollama embedding model
    embedding_dimension: int = 768

    # Vector Store
    vector_store: str = "pgvector"

    # Features
    enable_demo_mode: bool = True
    max_complaints_per_day: int = 1000

    # Incident intelligence
    incident_detection_window_hours: int = 48
    incident_similarity_threshold: float = 0.62
    incident_min_cluster_size: int = 3
    incident_top_k: int = 25
    incident_semantic_weight: float = 0.55
    incident_category_weight: float = 0.15
    incident_context_weight: float = 0.20
    incident_time_weight: float = 0.10
    incident_anomaly_baseline_days: int = 7

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

if settings.database_url.startswith("sqlite:///"):
    sqlite_path = settings.database_url.removeprefix("sqlite:///")
    if sqlite_path.startswith("./") or not Path(sqlite_path).is_absolute():
        resolved_sqlite_path = Path(__file__).resolve().parents[2] / sqlite_path.lstrip("./")
        settings.database_url = f"sqlite:///{resolved_sqlite_path.as_posix()}"
