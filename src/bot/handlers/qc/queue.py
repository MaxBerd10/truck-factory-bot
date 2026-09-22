"""QC — Tekshirish navbati."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsQC
from src.bot.keyboards import qc_queue_keyboard
from src.services.qc_service import get_qc_queue


router = Router(name="qc_queue")


# ==== "Tekshirish navbati" ====
@router.message(IsQC(), F.text == "🔔 Tekshirish navbati")
async def show_queue(
    message: Message,
    session: AsyncSession,
):
    """Navbatni ko'rsatish."""
    await _send_queue(message, session)


# ==== Yangilash ====
@router.callback_query(IsQC(), F.data == "qc_refresh")
async def refresh_queue(
    callback: CallbackQuery,
    session: AsyncSession,
):
    """Navbatni yangilash."""
    await callback.answer("🔄 Yangilanmoqda...")
    await _edit_queue(callback, session)


# ==== Yordamchi ====
async def _send_queue(
    message: Message,
    session: AsyncSession,
) -> None:
    """Navbatni yuborish."""
    steps = await get_qc_queue(session)

    if not steps:
        await message.answer(
            "🎉 <b>Navbat bo'sh!</b>\n\n"
            "✅ Barcha ishlar tekshirilgan.\n\n"
            "💡 Yangi ish kelganda sizga xabar beramiz.",
        )
        return

    text = (
        f"🔔 <b>Tekshirish navbati</b>\n\n"
        f"📊 Jami: <b>{len(steps)}</b> ta ish\n\n"
        f"👇 Tekshirish uchun ishni tanlang:"
    )

    await message.answer(
        text,
        reply_markup=qc_queue_keyboard(steps),
    )


async def _edit_queue(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Navbatni tahrirlash."""
    steps = await get_qc_queue(session)

    if not steps:
        try:
            await callback.message.edit_text(
                "🎉 <b>Navbat bo'sh!</b>\n\n"
                "✅ Barcha ishlar tekshirilgan.\n\n"
                "💡 Yangi ish kelganda sizga xabar beramiz.",
            )
        except Exception:
            await callback.message.answer(
                "🎉 <b>Navbat bo'sh!</b>\n\n"
                "✅ Barcha ishlar tekshirilgan.",
            )
        return

    text = (
        f"🔔 <b>Tekshirish navbati</b>\n\n"
        f"📊 Jami: <b>{len(steps)}</b> ta ish\n\n"
        f"👇 Tekshirish uchun ishni tanlang:"
    )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=qc_queue_keyboard(steps),
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=qc_queue_keyboard(steps),
        )
