"""Dispatcher ni sozlash."""
from aiogram import Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot.handlers import setup_handlers
from src.bot.middlewares import DbSessionMiddleware, UserMiddleware
from src.database.engine import async_session_maker


def create_dispatcher() -> Dispatcher:
    """Dispatcher ni yaratish va sozlash."""
    # FSM storage (hozircha xotirada)
    storage = MemoryStorage()

    dp = Dispatcher(storage=storage)

    # ==== Middleware lar (tartib muhim!) ====
    dp.update.outer_middleware(
        DbSessionMiddleware(session_maker=async_session_maker)
    )
    dp.update.middleware(UserMiddleware())

    # ==== Router lar ====
    dp.include_router(setup_handlers())

    return dp


def default_bot_properties() -> DefaultBotProperties:
    """Bot uchun standart sozlamalar."""
    return DefaultBotProperties(parse_mode=ParseMode.HTML)
