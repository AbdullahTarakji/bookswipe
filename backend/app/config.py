from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "BookSwipe API"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./bookswipe.db"

    # JWT
    secret_key: str = "change-me-in-production-use-a-real-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Google Books API
    google_books_api_url: str = "https://www.googleapis.com/books/v1/volumes"
    google_books_api_key: str = ""
    google_books_cache_ttl: int = 3600  # 1 hour

    # Rate limiting
    rate_limit_requests: int = 60
    rate_limit_window: int = 60  # seconds

    # CORS
    cors_origins: list[str] = ["*"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
