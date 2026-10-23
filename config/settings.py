from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file.

    Sensitive fields use `SecretStr` to prevent accidental exposure
    in logs, tracebacks, or API responses. To retrieve the raw string value:
    `settings.DEEPSEEK_API_KEY.get_secret_value()`
    """

    DEEPSEEK_API_KEY: SecretStr = Field(
        default=SecretStr(""),
        description="DeepSeek API key used for safety triage and roast generation",
    )
    HMAC_SECRET_KEY: SecretStr = Field(
        default=SecretStr(""),
        description="Secret key for pseudonymous user_key derivation via HMAC-SHA256",
    )
    TELEGRAM_BOT_TOKEN: SecretStr = Field(
        default=SecretStr(""),
        description="Telegram bot token issued by BotFather",
    )

    REDIS_URL: SecretStr = Field(
        default=SecretStr("redis://localhost:6379/0"),
        description="Redis / Upstash connection URL (SecretStr to protect inline credentials)",
    )
    DATABASE_URL: SecretStr = Field(
        default=SecretStr(""),
        description="Neon PostgreSQL pooled connection string",
    )


    TELEGRAM_BOT_USERNAME: str = Field(
        default="HotMicBot",
        description="Telegram bot username (without @) for the Web Login Widget",
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


# Global instance accessible throughout the project
settings = get_settings()

