"""Bot ishga tushirish (entry point)."""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot.handlers import setup_handlers
from src.bot.middlewares.db import DbSessionMiddleware
from src.bot.middlewares.user import UserMiddleware
from src.config import settings
from src.scheduler import setup_scheduler, stop_scheduler
from src.utils.logger import logger


# SQLAlchemy logging ni kamaytirish
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


async def main() -> None:
    """Asosiy funksiya."""
    # Bot
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Bot ma'lumotlarini tekshirish
    try:
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot tasdiqlandi: @{bot_info.username}")
    except Exception as e:
        logger.error(f"❌ Bot tokeni xato: {e}")
        await bot.session.close()
        sys.exit(1)

    # Dispatcher
    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares (tartib muhim!)
    # 1. DB session — eng tashqi
    dp.update.middleware(DbSessionMiddleware())
    # 2. User — DB dan user ni yuklaydi
    dp.update.middleware(UserMiddleware())

    # Handlers
    main_router = setup_handlers()
    dp.include_router(main_router)

    # Scheduler (kunlik hisobot va boshqalar)
    setup_scheduler(bot)

    # Botni ishga tushirish
    logger.info("🚀 Bot polling boshlandi.")

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        # Tozalash
        stop_scheduler()
        await bot.session.close()
        logger.info("👋 Bot to'xtatildi.")


def run() -> None:
    """Entry point (sync wrapper)."""
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⛔ Bot to'xtatildi (foydalanuvchi tomonidan).")


if __name__ == "__main__":
    run()
