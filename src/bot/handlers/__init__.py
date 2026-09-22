"""Handlers."""
from aiogram import Router

from src.bot.handlers.admin import get_admin_router
from src.bot.handlers.common import router as common_router
from src.bot.handlers.registration import router as registration_router
from src.bot.handlers.worker import get_worker_router


def setup_handlers() -> Router:
    """Barcha handlerlarni birlashtirib, asosiy routerni qaytaradi."""
    main_router = Router(name="main")

    # Tartib MUHIM:
    # 1. Registration (deep link)
    main_router.include_router(registration_router)

    # 2. Worker
    main_router.include_router(get_worker_router())

    # 3. Admin
    main_router.include_router(get_admin_router())

    # 4. Umumiy (start, help, id) — oxirgi
    main_router.include_router(common_router)

    return main_router
