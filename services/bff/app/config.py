from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    crm_backend_url: str = "http://crm-backend:8000"
    ecommerce_backend_url: str = "http://ecommerce-backend:8001"
    frontend_origin: str = "https://crm.felbatista.tech"
    secret_key: str = "change-me-in-production"
    app_env: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
