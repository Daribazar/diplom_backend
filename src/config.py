from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings."""

    APP_NAME: str = "Agentic ai student support system"
    APP_ENV: str = "development"
    DEBUG: bool = True
    CORS_ALLOW_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://172.18.0.6:3000",
    ]
    SECRET_KEY: str

    DATABASE_URL: str
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 өдөр (30 * 24 * 60)

    # OpenAI
    OPENAI_API_KEY: str

    # Anthropic
    ANTHROPIC_API_KEY: str

    # LLM
    DEFAULT_LLM_PROVIDER: str = "openai"  # "openai" or "claude"

    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "./uploads"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
