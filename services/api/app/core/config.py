"""Application configuration, loaded from environment variables.

Local development uses a .env file at the repository root (never committed).
All settings can be overridden by real environment variables, which is how
containers and Kubernetes inject configuration.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    app_env: str = "development"  # development | test | production
    log_level: str = "INFO"

    # API
    api_host: str = "0.0.0.0"  # noqa: S104 — containerized service binds all interfaces intentionally
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:8080,http://localhost:5000"

    # Security (used from Phase 3; defined now so env layout is stable)
    jwt_secret_key: str = "change-me-generate-a-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "expense_tracker"
    postgres_user: str = "expense_app"
    postgres_password: str = ""

    # Redis (rate limiting / cache) — optional; rate limiting is disabled when unset.
    redis_url: str | None = None

    @property
    def database_url(self) -> str:
        """Async SQLAlchemy connection URL assembled from discrete env vars."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance. Call get_settings.cache_clear() in tests after
    monkeypatching environment variables."""
    return Settings()
