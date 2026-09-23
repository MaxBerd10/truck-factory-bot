"""QC — Statistika."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsQC, text_key
from src.database.models.user import User
from src.services.i18n_service import _
from src.services.stats_service import get_qc_full_stats


router = Router(name="qc_stats")


@router.message(IsQC(), text_key("qc.menu_stats"))
async def show_stats(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """QC statistikasini ko'rsatish."""
    await _send_stats(message, user, session)


@router.callback_query(IsQC(), F.data == "qc_stats_view")
async def show_stats_callback(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Statistikani callback orqali ko'rsatish."""
    await callback.answer()
    await _send_stats(callback.message, user, session)


async def _send_stats(
    message,
    user: User,
    session: AsyncSession,
) -> None:
    """Statistikani yuborish."""
    lang = user.language or "uz"
    stats = await get_qc_full_stats(session, user.id)

    if stats["total"] == 0:
        await message.answer(
            _("qc.stats_empty", language=lang),
        )
        return

    text = (
        f"{_('qc.stats_title', language=lang)}\n\n"
        f"📈 <b>Umumiy:</b>\n"
        f"  • {_('qc.stats_total', language=lang, count=stats['total'])}\n"
        f"  • {_('qc.stats_approved', language=lang, count=stats['approved'])}\n"
        f"  • {_('qc.stats_rejected', language=lang, count=stats['rejected'])}\n\n"
        f"📊 <b>{_('qc.stats_approve_rate', language=lang, rate=stats['approve_rate'])}</b>\n\n"
    )

    if stats["total"] > 0:
        approved = stats["approved"]
        total = stats["total"]
        filled = int((approved / total) * 10)
        bar = "█" * filled + "░" * (10 - filled)
        text += f"<code>{bar}</code> {approved}/{total}\n"

    await message.answer(text)
