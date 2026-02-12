"""Application settings loaded from environment variables and .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the BookSwipe API."""
    app_name: str = "BookSwipe API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = "sqlite:///./bookswipe.db"

    # Connection pool (PostgreSQL only, ignored for SQLite)
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    # JWT
    secret_key: str = "change-me-in-production-use-a-real-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    jwt_issuer: str = "bookswipe-api"
    jwt_audience: str = "bookswipe-client"

    # Google Books API
    google_books_api_url: str = "https://www.googleapis.com/books/v1/volumes"
    google_books_api_key: str = ""
    google_books_cache_ttl: int = 3600  # 1 hour

    # Rate limiting (Google Books per-user)
    rate_limit_requests: int = 60
    rate_limit_window: int = 60  # seconds

    # Rate limiting (API endpoints)
    auth_rate_limit: str = "5/minute"
    api_rate_limit: str = "30/minute"

    # CORS
    cors_origins: list[str] = ["*"]

    # OAuth
    google_client_id: str = ""
    apple_client_id: str = ""

    # Password policy
    password_min_length: int = 8

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()

# Warn if using default secret key in production
if settings.secret_key == "change-me-in-production-use-a-real-secret-key" and settings.is_production:
    raise RuntimeError("SECRET_KEY must be changed for production!")
