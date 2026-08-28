from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:123@localhost:5433/postgres"

    # Redis
    redis_url: str = "redis://localhost:6380/0"

    # Groq / LLM
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_model_fallbacks: list[str] = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
    ]

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # App
    app_env: str = "development"
    frontend_origin: str = "http://localhost:5173"
    secret_key: str = "change-me-in-production"

    # Session
    session_ttl_seconds: int = 604800  # 7 days

    # AwesomeAPI
    awesomeapi_key: str = ""

    # Sentry
    sentry_dsn: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
