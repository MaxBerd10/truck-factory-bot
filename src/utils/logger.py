"""Loguru asosida sozlangan logger."""
import logging as std_logging
import sys
from pathlib import Path

from loguru import logger

from src.config import settings


# ==================== SHOVQINLI LOGLARNI O'CHIRISH ====================
std_logging.getLogger("sqlalchemy").setLevel(std_logging.WARNING)
std_logging.getLogger("sqlalchemy.engine").setLevel(std_logging.WARNING)
std_logging.getLogger("sqlalchemy.engine.Engine").setLevel(std_logging.WARNING)
std_logging.getLogger("sqlalchemy.pool").setLevel(std_logging.WARNING)
std_logging.getLogger("sqlalchemy.orm").setLevel(std_logging.WARNING)
std_logging.getLogger("aiogram").setLevel(std_logging.WARNING)
std_logging.getLogger("aiogram.dispatcher").setLevel(std_logging.WARNING)
std_logging.getLogger("aiogram.event").setLevel(std_logging.WARNING)
std_logging.getLogger("apscheduler").setLevel(std_logging.WARNING)
std_logging.getLogger("asyncio").setLevel(std_logging.WARNING)


# Standart handlerni olib tashlaymiz
logger.remove()


# ==== 1. Konsolga chiqarish (rangli) ====
logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ),
    colorize=True,
    backtrace=True,
    diagnose=settings.ENVIRONMENT == "development",
)


# ==== 2. Faylga yozish (rotatsiya bilan) ====
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.add(
    LOG_DIR / "bot_{time:YYYY-MM-DD}.log",
    level="DEBUG" if settings.ENVIRONMENT == "development" else "INFO",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    ),
    rotation="00:00",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
    backtrace=True,
    diagnose=False,
)


# ==== 3. Xatolar uchun alohida fayl ====
logger.add(
    LOG_DIR / "errors_{time:YYYY-MM-DD}.log",
    level="ERROR",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}\n{exception}"
    ),
    rotation="00:00",
    retention="90 days",
    compression="zip",
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
)


__all__ = ["logger"]
