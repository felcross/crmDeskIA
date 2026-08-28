from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:123@ecom-postgres:5432/ecommerce"
    app_env: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
