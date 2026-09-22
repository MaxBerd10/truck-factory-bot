"""Handlers."""
from aiogram import Router

from src.bot.handlers.admin import get_admin_router
from src.bot.handlers.common import router as common_router
from src.bot.handlers.registration import router as registration_router


def setup_handlers() -> Router:
    """Barcha handlerlarni birlashtirib, asosiy routerni qaytaradi."""
    main_router = Router(name="main")

    # Tartib MUHIM:
    # 1. Registration (deep link) — eng oldin
    main_router.include_router(registration_router)

    # 2. Admin handlerlar
    main_router.include_router(get_admin_router())

    # 3. Umumiy handlerlar (start, help, id) — oxirgi
    main_router.include_router(common_router)

    return main_router
