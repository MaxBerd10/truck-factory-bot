"""Ishchi — Tarixim."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsWorker
from src.bot.keyboards import worker_history_keyboard
from src.database.models.user import User
from src.services.stats_service import get_worker_full_stats
from src.services.truck_step_service import get_worker_history


router = Router(name="worker_history")


# ==== "Tarixim" ====
@router.message(IsWorker(), F.text == "📜 Tarixim")
async def show_history(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """Ishchining tarixini ko'rsatish."""
    await _send_history(message, user, session)


# ==== Yangilash ====
@router.callback_query(IsWorker(), F.data == "worker_history")
async def refresh_history(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Tarixni yangilash."""
    await callback.answer()
    await _edit_history(callback, user, session)


# ==== Yordamchi ====
async def _send_history(
    message: Message,
    user: User,
    session: AsyncSession,
) -> None:
    """Tarixni yuborish."""
    stats = await get_worker_full_stats(session, user.id)
    history = await get_worker_history(session, user.id)

    if stats["total"] == 0:
        await message.answer(
            "📜 <b>Tarixim</b>\n\n"
            "Hozircha tarix bo'sh.\n\n"
            "<i>Ish yuborganingizdan keyin bu yerda ko'rinadi.</i>",
        )
        return

    text = (
        f"📜 <b>Tarixim</b>\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"  • Jami: <b>{stats['total']}</b>\n"
        f"  • ✅ Tasdiqlangan: <b>{stats['approved']}</b>\n"
        f"  • 🔍 Tekshirilmoqda: <b>{stats['in_review']}</b>\n"
        f"  • ❌ Rad etilgan: <b>{stats['rejected']}</b>\n"
        f"  • 📈 Muvaffaqiyat: <b>{stats['success_rate']}%</b>\n\n"
        f"📋 <b>Oxirgi ishlar:</b>"
    )

    await message.answer(
        text,
        reply_markup=worker_history_keyboard(history),
    )


async def _edit_history(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
) -> None:
    """Tarixni tahrirlash."""
    stats = await get_worker_full_stats(session, user.id)
    history = await get_worker_history(session, user.id)

    if stats["total"] == 0:
        try:
            await callback.message.edit_text(
                "📜 <b>Tarixim</b>\n\n"
                "Hozircha tarix bo'sh.",
            )
        except Exception:
            await callback.message.answer(
                "📜 <b>Tarixim</b>\n\n"
                "Hozircha tarix bo'sh.",
            )
        return

    text = (
        f"📜 <b>Tarixim</b>\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"  • Jami: <b>{stats['total']}</b>\n"
        f"  • ✅ Tasdiqlangan: <b>{stats['approved']}</b>\n"
        f"  • 🔍 Tekshirilmoqda: <b>{stats['in_review']}</b>\n"
        f"  • ❌ Rad etilgan: <b>{stats['rejected']}</b>\n"
        f"  • 📈 Muvaffaqiyat: <b>{stats['success_rate']}%</b>\n\n"
        f"📋 <b>Oxirgi ishlar:</b>"
    )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=worker_history_keyboard(history),
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=worker_history_keyboard(history),
        )
