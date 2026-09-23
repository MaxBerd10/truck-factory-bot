"""Ishchi — Statistika."""
from aiogram import Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsWorker, text_key
from src.database.models.user import User
from src.services.i18n_service import _, get_step_name
from src.services.stats_service import get_worker_full_stats


router = Router(name="worker_stats")


@router.message(IsWorker(), text_key("worker.menu_stats"))
async def show_stats(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """Ishchi statistikasini ko'rsatish."""
    lang = user.language or "uz"
    stats = await get_worker_full_stats(session, user.id)
    step_name = (
        get_step_name(user.step_number, lang) if user.step_number else "—"
    )

    if stats["total"] == 0:
        await message.answer(
            _("worker.stats_empty", language=lang, step=step_name),
        )
        return

    text = (
        f"{_('worker.stats_title', language=lang)}\n\n"
        f"🔧 {step_name}\n\n"
        f"📈 <b>Umumiy:</b>\n"
        f"  • {_('worker.stats_jobs', language=lang, count=stats['total'])}\n"
        f"  • {_('worker.stats_approved', language=lang, count=stats['approved'])}\n"
        f"  • {_('worker.stats_in_review', language=lang, count=stats['in_review'])}\n"
        f"  • {_('worker.stats_rejected', language=lang, count=stats['rejected'])}\n\n"
        f"📊 <b>{_('worker.stats_success_rate', language=lang, rate=stats['success_rate'])}</b>\n\n"
    )

    if stats["total"] > 0:
        approved = stats["approved"]
        total = stats["total"]
        filled = int((approved / total) * 10)
        bar = "█" * filled + "░" * (10 - filled)
        text += f"<code>{bar}</code> {approved}/{total}\n"

    await message.answer(text)
