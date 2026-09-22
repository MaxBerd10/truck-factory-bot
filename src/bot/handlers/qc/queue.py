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
    await callback.answer()
    await _edit_queue(callback, session)


# ==== Yordamchi ====
async def _send_queue(
    message: Message,
    session: AsyncSession,
) -> None:
    """Yangi xabar bilan navbatni yuborish."""
    steps = await get_qc_queue(session)

    if not steps:
        await message.answer(
            "🔔 <b>Tekshirish navbati</b>\n\n"
            "✅ Navbat bo'sh.\n\n"
            "<i>Yangi ishlar kelganda sizga xabar beramiz.</i>",
        )
        return

    text = (
        f"🔔 <b>Tekshirish navbati</b>\n\n"
        f"📊 Jami: <b>{len(steps)}</b> ta ish\n\n"
        f"Tekshirish uchun ishni tanlang:"
    )

    await message.answer(
        text,
        reply_markup=qc_queue_keyboard(steps),
    )


async def _edit_queue(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Mavjud xabarni tahrirlab, navbatni yangilash.

    Agar xabar edit qilib bo'lmasa (rasm bilan), yangi xabar yuboramiz.
    """
    steps = await get_qc_queue(session)

    if not steps:
        text = (
            "🔔 <b>Tekshirish navbati</b>\n\n"
            "✅ Navbat bo'sh.\n\n"
            "<i>Yangi ishlar kelganda sizga xabar beramiz.</i>"
        )
        try:
            await callback.message.edit_text(text)
        except Exception:
            await callback.message.answer(text)
        return

    text = (
        f"🔔 <b>Tekshirish navbati</b>\n\n"
        f"📊 Jami: <b>{len(steps)}</b> ta ish\n\n"
        f"Tekshirish uchun ishni tanlang:"
    )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=qc_queue_keyboard(steps),
        )
    except Exception:
        # Rasmli xabar yoki edit qilib bo'lmaydigan xabar
        await callback.message.answer(
            text,
            reply_markup=qc_queue_keyboard(steps),
        )
