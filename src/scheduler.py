"""APScheduler — kunlik hisobot uchun."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.database.session import async_session_maker
from src.services.report_service import (
    get_all_admin_telegram_ids,
    send_daily_report,
)
from src.utils.logger import logger


scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")


async def daily_report_job(bot) -> None:
    """Kunlik hisobot job i."""
    try:
        async with async_session_maker() as session:
            admin_ids = await get_all_admin_telegram_ids(session)
            if not admin_ids:
                logger.warning("⚠️ Kunlik hisobot: admin topilmadi")
                return
            await send_daily_report(session, bot, admin_ids)
    except Exception as e:
        logger.exception(f"❌ Kunlik hisobot xatosi: {e}")


def setup_scheduler(bot) -> None:
    """Schedulerni sozlash."""
    scheduler.add_job(
        daily_report_job,
        trigger=CronTrigger(hour=18, minute=0),
        args=[bot],
        id="daily_report",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("⏰ Scheduler ishga tushdi: kunlik hisobot 18:00")


def stop_scheduler() -> None:
    """Schedulerni to'xtatish."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("⏰ Scheduler to'xtatildi")
