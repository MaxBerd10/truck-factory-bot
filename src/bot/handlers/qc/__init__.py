"""QC handlers."""
from aiogram import Router

from src.bot.handlers.qc.history import router as history_router
from src.bot.handlers.qc.queue import router as queue_router
from src.bot.handlers.qc.review import router as review_router
from src.bot.handlers.qc.stats import router as stats_router


def get_qc_router() -> Router:
    """QC routerlarini birlashtirish."""
    router = Router(name="qc")
    router.include_router(queue_router)
    router.include_router(review_router)
    router.include_router(history_router)
    router.include_router(stats_router)
    return router
