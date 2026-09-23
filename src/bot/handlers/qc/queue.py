"""QC — Tekshirish navbati."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsQC, text_key
from src.bot.keyboards import qc_queue_keyboard
from src.database.models.user import User
from src.services.i18n_service import _
from src.services.qc_service import get_qc_queue


router = Router(name="qc_queue")


# ==================== "Tekshirish navbati" ====================
@router.message(IsQC(), text_key("qc.menu_queue"))
async def show_queue(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """Navbatni ko'rsatish."""
    await _send_queue(message, user, session)


# ==================== Yangilash ====================
@router.callback_query(IsQC(), F.data == "qc_refresh")
async def refresh_queue(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Navbatni yangilash."""
    lang = user.language or "uz"
    await callback.answer(_("common.loading", language=lang))
    await _edit_queue(callback, user, session)


# ==================== Yordamchi ====================
async def _send_queue(
    message: Message,
    user: User,
    session: AsyncSession,
) -> None:
    """Navbatni yuborish."""
    lang = user.language or "uz"
    steps = await get_qc_queue(session)

    if not steps:
        await message.answer(
            _("qc.queue_empty", language=lang),
        )
        return

    text = (
        f"{_('qc.queue_title', language=lang)}\n\n"
        f"{_('qc.queue_total', language=lang, count=len(steps))}\n\n"
        f"{_('qc.queue_choose', language=lang)}"
    )

    await message.answer(
        text,
        reply_markup=qc_queue_keyboard(steps, lang),
    )


async def _edit_queue(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
) -> None:
    """Navbatni tahrirlash."""
    lang = user.language or "uz"
    steps = await get_qc_queue(session)

    if not steps:
        try:
            await callback.message.edit_text(
                _("qc.queue_empty", language=lang),
            )
        except Exception:
            await callback.message.answer(
                _("qc.queue_empty", language=lang),
            )
        return

    text = (
        f"{_('qc.queue_title', language=lang)}\n\n"
        f"{_('qc.queue_total', language=lang, count=len(steps))}\n\n"
        f"{_('qc.queue_choose', language=lang)}"
    )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=qc_queue_keyboard(steps, lang),
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=qc_queue_keyboard(steps, lang),
        )
