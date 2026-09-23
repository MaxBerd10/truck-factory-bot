"""Sozlamalar (config)."""
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Bot sozlamalari."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # ==== Bot ====
    BOT_TOKEN: str = Field(..., description="Telegram bot token")
    ADMIN_IDS: list[int] = Field(default_factory=list, description="Admin ID lar")

    # ==== Environment ====
    ENVIRONMENT: Literal["development", "production", "testing"] = Field(
        default="development"
    )
    LOG_LEVEL: str = Field(default="INFO")

    # ==== Database ====
    POSTGRES_USER: str = Field(default="truckbot")
    POSTGRES_PASSWORD: str = Field(default="truckbot")
    POSTGRES_DB: str = Field(default="truck_factory")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)

    DB_URL: str = Field(default="")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # ==== Media ====
    MEDIA_ROOT: str = Field(default="media")

    # ==== Properties ====
    @property
    def is_development(self) -> bool:
        """Development muhitda ishlayaptimi?"""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Production muhitda ishlayaptimi?"""
        return self.ENVIRONMENT == "production"

    @property
    def media_path(self) -> Path:
        """Media papkasi (Path)."""
        return Path(self.MEDIA_ROOT)

    def model_post_init(self, __context) -> None:
        """DB_URL avtomatik yasash (agar bo'sh bo'lsa)."""
        if not self.DB_URL:
            object.__setattr__(
                self,
                "DB_URL",
                f"postgresql+asyncpg://{self.POSTGRES_USER}:"
                f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
                f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}",
            )


# Global settings instance
settings = Settings()  # type: ignore[call-arg]
