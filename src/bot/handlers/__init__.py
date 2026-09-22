"""Handlers."""
from aiogram import Router

from src.bot.handlers.admin import get_admin_router
from src.bot.handlers.common import router as common_router
from src.bot.handlers.qc import get_qc_router
from src.bot.handlers.registration import router as registration_router
from src.bot.handlers.settings import router as settings_router
from src.bot.handlers.worker import get_worker_router


def setup_handlers() -> Router:
    """Barcha handlerlarni birlashtirib, asosiy routerni qaytaradi."""
    main_router = Router(name="main")

    main_router.include_router(registration_router)
    main_router.include_router(get_worker_router())
    main_router.include_router(get_qc_router())
    main_router.include_router(get_admin_router())
    main_router.include_router(settings_router)
    main_router.include_router(common_router)

    return main_router
