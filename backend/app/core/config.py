from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "News Aggregator"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./news_aggregator.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM Provider — supports any OpenAI-compatible API
    LLM_ENABLED: bool = True               # Set false to use extractive-only (no API calls)
    LLM_PROVIDER: str = "openai"           # openai, ollama, kimi, deepseek, etc.
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"         # or: deepseek-chat, moonshot-v1, qwen2.5, etc.

    # Custom base URL for non-OpenAI providers:
    #   Ollama:   http://localhost:11434/v1
    #   Kimi:     https://api.moonshot.cn/v1
    #   DeepSeek: https://api.deepseek.com/v1
    LLM_BASE_URL: Optional[str] = None

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # RSS / News
    DEFAULT_REFRESH_INTERVAL_MINUTES: int = 30
    MAX_ARTICLES_PER_SOURCE: int = 5
    MAX_ARTICLES_TOTAL: int = 5

    # Digest
    MORNING_BRIEFING_TIME: str = "07:00"

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()