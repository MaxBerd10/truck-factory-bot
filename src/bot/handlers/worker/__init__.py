"""Worker handlers."""
from aiogram import Router

from src.bot.handlers.worker.history import router as history_router
from src.bot.handlers.worker.stats import router as stats_router
from src.bot.handlers.worker.submit import router as submit_router
from src.bot.handlers.worker.tasks import router as tasks_router


def get_worker_router() -> Router:
    """Worker routerlarini birlashtirish."""
    router = Router(name="worker")
    router.include_router(tasks_router)
    router.include_router(submit_router)
    router.include_router(history_router)
    router.include_router(stats_router)
    return router
