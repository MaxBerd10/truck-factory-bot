"""Loyiha sozlamalari (pydantic-settings asosida)."""
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Barcha sozlamalar .env fayldan o'qiladi."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==== BOT ====
    BOT_TOKEN: str = Field(..., description="Telegram bot token")
    BOT_USERNAME: str = Field(default="", description="Bot username (@ belgisisiz)")

    # ==== ADMIN ====
    ADMIN_IDS: list[int] = Field(
        default_factory=list,
        description="Birinchi adminlar Telegram ID lari",
    )

    # ==== DATABASE ====
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    DB_URL: str

    # ==== REDIS ====
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str

    # ==== APP ====
    ENVIRONMENT: Literal["development", "production"] = "development"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    TIMEZONE: str = "Asia/Tashkent"

    # ==== MEDIA ====
    MEDIA_ROOT: str = "/app/media"
    MAX_FILE_SIZE_MB: int = 50

    # ==== VALIDATORS ====
    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        """'123,456' -> [123, 456]"""
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, int):
            return [v]
        return v

    @field_validator("BOT_TOKEN")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Token formatini tekshirish."""
        if ":" not in v or len(v) < 30:
            raise ValueError(
                "BOT_TOKEN noto'g'ri formatda. "
                "@BotFather dan yangi token oling."
            )
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Sozlamalarni bir marta yuklab, cache da saqlaydi."""
    return Settings()


settings = get_settings()
