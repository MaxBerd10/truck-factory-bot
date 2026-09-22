"""Bot ning asosiy kirish nuqtasi."""
import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramUnauthorizedError

from src.bot.dispatcher import create_dispatcher, default_bot_properties
from src.config import settings
from src.database.engine import close_engine
from src.utils.logger import logger


async def main() -> None:
    """Botni ishga tushirish."""
    logger.info("=" * 60)
    logger.info("🚛 Truck Factory Bot ishga tushmoqda...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Bot: @{settings.BOT_USERNAME}")
    logger.info(f"Adminlar: {len(settings.ADMIN_IDS)} ta")
    logger.info("=" * 60)

    # Bot
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=default_bot_properties(),
    )

    # Bot ma'lumotlarini tekshirish
    try:
        me = await bot.get_me()
        logger.success(f"✅ Bot tasdiqlandi: @{me.username} (id={me.id})")
    except TelegramUnauthorizedError:
        logger.error("❌ BOT_TOKEN noto'g'ri! @BotFather dan yangi token oling.")
        return
    except Exception as e:
        logger.error(f"❌ Bot bilan ulanishda xato: {e}")
        return

    # Dispatcher
    dp = create_dispatcher()

    logger.success("🚀 Bot polling boshlandi. Telegramda /start bosing.")

    try:
        # Webhook ni tozalash (agar avval ishlatilgan bo'lsa)
        await bot.delete_webhook(drop_pending_updates=True)
        # Polling boshlash
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await close_engine()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Xayr!")
