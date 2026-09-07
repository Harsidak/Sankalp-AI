"""
Application configuration via Pydantic Settings.

All configuration is loaded from environment variables (or .env file).
Validates required fields at startup — app fails fast if misconfigured.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the entire application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "SanKalp"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "CHANGE_ME_IN_PRODUCTION"

    # --- Database (MySQL) ---
    database_url: str = "mysql+aiomysql://root:password@localhost:3306/sankalp"

    # --- Authentication ---
    jwt_secret_key: str = "CHANGE_ME_JWT_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # --- Google OAuth 2.0 ---
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = "http://localhost:5173/auth/google/callback"

    # --- AI / LLM ---
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # NVIDIA NIM speaks the OpenAI wire format, so it needs no SDK of its own --
    # only a key and a base URL. Kept as separate settings rather than
    # overloading openai_api_key so both providers can be configured at once.
    nvidia_api_key: Optional[str] = None
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"

    default_llm_provider: str = "openai"
    default_llm_model: str = "gpt-4o-mini"

    # --- CORS ---
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # --- Redis (Optional) ---
    redis_url: Optional[str] = None

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings singleton.
    Call this instead of constructing Settings() directly.
    """
    return Settings()
