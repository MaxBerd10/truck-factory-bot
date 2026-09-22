"""QC — Statistika."""
from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsQC
from src.database.models.user import User
from src.services.stats_service import get_qc_full_stats


router = Router(name="qc_stats")


@router.message(IsQC(), F.text == "📊 Statistika")
async def show_stats(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """QC statistikasini ko'rsatish."""
    stats = await get_qc_full_stats(session, user.id)

    if stats["total"] == 0:
        await message.answer(
            "📊 <b>Statistika</b>\n\n"
            "📋 Hozircha ma'lumot yo'q.\n\n"
            "💡 Ish tekshirganingizdan keyin statistika paydo bo'ladi.",
        )
        return

    text = (
        f"📊 <b>Statistika</b>\n\n"
        f"📈 <b>Umumiy:</b>\n"
        f"  • Jami tekshirilgan: <b>{stats['total']}</b>\n"
        f"  • ✅ Tasdiqlangan: <b>{stats['approved']}</b>\n"
        f"  • ❌ Rad etilgan: <b>{stats['rejected']}</b>\n\n"
        f"📊 <b>Tasdiqlash foizi:</b> <b>{stats['approve_rate']}%</b>\n\n"
    )

    # Progress bar
    if stats["total"] > 0:
        approved = stats["approved"]
        total = stats["total"]
        filled = int((approved / total) * 10)
        bar = "█" * filled + "░" * (10 - filled)
        text += f"<code>{bar}</code> {approved}/{total}\n"

    await message.answer(text)
