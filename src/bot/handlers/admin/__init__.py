"""Admin handlers."""
from aiogram import Router

from src.bot.handlers.admin.invites import router as invites_router
from src.bot.handlers.admin.trucks import router as trucks_router
from src.bot.handlers.admin.user_add import router as user_add_router
from src.bot.handlers.admin.users import router as users_router


def get_admin_router() -> Router:
    """Admin routerlarini birlashtirish."""
    router = Router(name="admin")
    router.include_router(users_router)
    router.include_router(user_add_router)
    router.include_router(invites_router)
    router.include_router(trucks_router)
    return router
