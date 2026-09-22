"""Ishchi — Statistika."""
from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsWorker
from src.database.models.user import User
from src.services.stats_service import get_worker_full_stats
from src.utils.constants import STEP_NAMES


router = Router(name="worker_stats")


@router.message(IsWorker(), F.text == "📊 Statistika")
async def show_stats(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """Ishchi statistikasini ko'rsatish."""
    stats = await get_worker_full_stats(session, user.id)

    step_name = STEP_NAMES.get(user.step_number, f"Step {user.step_number}")

    if stats["total"] == 0:
        await message.answer(
            f"📊 <b>Statistika</b>\n\n"
            f"🔧 Bo'lim: {step_name}\n\n"
            f"📋 Hozircha ma'lumot yo'q.\n\n"
            f"💡 Ish yuborganingizdan keyin statistika paydo bo'ladi.",
        )
        return

    text = (
        f"📊 <b>Statistika</b>\n\n"
        f"🔧 Bo'lim: {step_name}\n\n"
        f"📈 <b>Umumiy:</b>\n"
        f"  • Jami ishlar: <b>{stats['total']}</b>\n"
        f"  • ✅ Tasdiqlangan: <b>{stats['approved']}</b>\n"
        f"  • 🔍 Tekshirilmoqda: <b>{stats['in_review']}</b>\n"
        f"  • ❌ Rad etilgan: <b>{stats['rejected']}</b>\n\n"
        f"📊 <b>Muvaffaqiyat:</b> <b>{stats['success_rate']}%</b>\n\n"
    )

    # Progress bar
    if stats["total"] > 0:
        approved = stats["approved"]
        total = stats["total"]
        filled = int((approved / total) * 10)
        bar = "█" * filled + "░" * (10 - filled)
        text += f"<code>{bar}</code> {approved}/{total}\n"

    await message.answer(text)

