from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurazione dell'applicazione caricata da variabili d'ambiente o file .env.
    
    I campi sensibili utilizzano `SecretStr` per prevenire leak accidentali
    in log, eccezioni o risposte API. Per accedere al valore stringa grezzo:
    `settings.DEEPSEEK_API_KEY.get_secret_value()`
    """

    # --- Credenziali e Chiavi Sensibili (SecretStr) ---
    DEEPSEEK_API_KEY: SecretStr = Field(
        ...,
        description="Chiave API DeepSeek per la pipeline di triage e roast",
    )
    HMAC_SECRET_KEY: SecretStr = Field(
        ...,
        description="Chiave segreta per la derivazione HMAC-SHA256 delle user_key",
    )
    TELEGRAM_BOT_TOKEN: SecretStr = Field(
        ...,
        description="Token del bot Telegram rilasciato da BotFather",
    )
    REDIS_URL: SecretStr = Field(
        default=SecretStr("redis://localhost:6379/0"),
        description="URL di connessione Redis / Upstash (SecretStr per proteggere credenziali inline)",
    )
    DATABASE_URL: SecretStr = Field(
        default=SecretStr(""),
        description="Stringa di connessione Neon PostgreSQL (pooled)",
    )

    # --- Configurazioni Pubbliche / Non Segrete ---
    TELEGRAM_WEBHOOK_URL: str = Field(
        default="",
        description="URL pubblico per il webhook di Telegram su Vercel",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Restituisce un'istanza singleton di Settings con cache LRU."""
    return Settings()


# Istanza globale accessibile nel progetto
settings = get_settings()
