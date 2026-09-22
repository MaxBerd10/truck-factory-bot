"""Ishchi — Tarixim."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsWorker
from src.bot.keyboards import worker_history_keyboard
from src.database.models.user import User
from src.services.truck_step_service import get_worker_history
from src.utils.constants import STEP_NAMES


router = Router(name="worker_history")


# ==== "Tarixim" ====
@router.message(IsWorker(), F.text == "📜 Tarixim")
async def show_history(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """Ishchining tarixini ko'rsatish."""
    history = await get_worker_history(session, user.id)

    if not history:
        await message.answer(
            "📜 <b>Tarixim</b>\n\n"
            "Hozircha tarix bo'sh.\n\n"
            "<i>Ish yuborganingizdan keyin bu yerda ko'rinadi.</i>",
        )
        return

    text = (
        f"📜 <b>Tarixim</b>\n\n"
        f"Jami: <b>{len(history)}</b> ta ish\n\n"
        f"Batafsil ko'rish uchun tanlang:"
    )

    await message.answer(
        text,
        reply_markup=worker_history_keyboard(history),
    )


# ==== Tarixni yangilash ====
@router.callback_query(IsWorker(), F.data == "worker_history")
async def refresh_history(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Tarixni yangilash."""
    await callback.answer()

    history = await get_worker_history(session, user.id)

    if not history:
        await callback.message.edit_text(
            "📜 <b>Tarixim</b>\n\n"
            "Hozircha tarix bo'sh.",
        )
        return

    text = (
        f"📜 <b>Tarixim</b>\n\n"
        f"Jami: <b>{len(history)}</b> ta ish\n\n"
        f"Batafsil ko'rish uchun tanlang:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=worker_history_keyboard(history),
    )
