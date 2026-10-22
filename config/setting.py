from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file.

    Sensitive fields are wrapped in `SecretStr` to prevent accidental exposure
    in logs, tracebacks, and prints. Use `.get_secret_value()` to retrieve the raw string.
    """
    DEEPSEEK_API_KEY: SecretStr = Field(
        ...,
        description="DeepSeek API key used for safety triage and roast generation",
    )
    HMAC_SECRET_KEY: SecretStr = Field(
        ...,
        description="Secret key for pseudonymous user_key derivation via HMAC-SHA256",
    )
    TELEGRAM_BOT_TOKEN: SecretStr = Field(
        ...,
        description="Telegram bot token issued by BotFather",
    )
    REDIS_URL: SecretStr = Field(
        default=SecretStr("redis://localhost:6379/0"),
        description="Redis connection URL for caching and rate limiting",
    )
    DATABASE_URL: SecretStr = Field(
        default=SecretStr(""),
        description="Neon PostgreSQL pooled connection string",
    )

    TELEGRAM_WEBHOOK_URL: str = Field(
        default="",
        description="Public URL endpoint for Telegram webhook on Vercel",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Returns a cached singleton instance of Settings."""
    return Settings()


setting = get_settings()
