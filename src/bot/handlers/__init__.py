"""Handlers."""
from aiogram import Router

from src.bot.handlers.admin import get_admin_router
from src.bot.handlers.common import router as common_router


def setup_handlers() -> Router:
    """Barcha handlerlarni birlashtirib, asosiy routerni qaytaradi."""
    main_router = Router(name="main")

    # Tartib muhim:
    # 1. Admin handlerlar (IsAdmin filtri bilan)
    main_router.include_router(get_admin_router())

    # 2. Umumiy handlerlar (start, help, id)
    main_router.include_router(common_router)

    return main_router
