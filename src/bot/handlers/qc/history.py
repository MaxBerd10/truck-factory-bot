"""QC — Tarixim."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsQC, text_key
from src.bot.keyboards import (
    qc_history_detail_keyboard,
    qc_history_keyboard,
)
from src.database.models.user import User
from src.services.i18n_service import _, get_priority_name, get_step_name
from src.services.qc_service import get_qc_history, get_step_for_review
from src.services.stats_service import get_qc_full_stats


router = Router(name="qc_history")


# ==================== "Tarixim" ====================
@router.message(IsQC(), text_key("qc.menu_history"))
async def show_history(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """QC tarixini ko'rsatish."""
    await _send_history(message, user, session)


# ==================== Yangilash ====================
@router.callback_query(IsQC(), F.data == "qc_history")
async def refresh_history(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Tarixni yangilash."""
    lang = user.language or "uz"
    await callback.answer(_("common.loading", language=lang))
    await _edit_history(callback, user, session)


# ==================== Tarix tafsiloti ====================
@router.callback_query(IsQC(), F.data.startswith("qc_history_view:"))
async def view_history_detail(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Tarix tafsilotini ko'rsatish."""
    lang = user.language or "uz"
    step_id = int(callback.data.split(":")[1])
    step = await get_step_for_review(session, step_id)

    if not step:
        await callback.answer(
            _("common.not_found", language=lang),
            show_alert=True,
        )
        return

    await callback.answer()

    truck = step.truck
    priority_name = get_priority_name(truck.priority, lang)
    step_name = get_step_name(step.step_number, lang)

    if step.is_approved:
        status_text = _("statuses.approved", language=lang)
    elif step.is_rejected:
        status_text = _("statuses.rejected", language=lang)
    else:
        status_text = _("statuses.in_review", language=lang)

    text = f"{_('qc.history_title', language=lang)}\n\n"
    text += f"🚛 <b>{truck.serial_number}</b>\n"
    text += f"🔧 <b>{step_name}</b>\n"
    text += f"🎯 {priority_name}\n\n"
    text += f"📊 {status_text}\n"

    if step.worker:
        text += f"👷 {step.worker.full_name}\n"

    if step.worker_comment:
        text += f"\n📝 <b>Izoh:</b>\n<i>{step.worker_comment}</i>\n"

    if step.qc_comment:
        text += f"\n❌ <b>Sabab:</b>\n<i>{step.qc_comment}</i>\n"

    if step.reviewed_at:
        text += f"\n🕐 {step.reviewed_at.strftime('%Y-%m-%d %H:%M')}"

    if step.media_type == "photo" and step.media_file_id:
        await callback.message.answer_photo(
            photo=step.media_file_id,
            caption=text,
            reply_markup=qc_history_detail_keyboard(lang),
        )
    else:
        await callback.message.answer(
            text,
            reply_markup=qc_history_detail_keyboard(lang),
        )


# ==================== Yordamchi ====================
async def _send_history(
    message: Message,
    user: User,
    session: AsyncSession,
) -> None:
    """Tarixni yuborish."""
    lang = user.language or "uz"
    stats = await get_qc_full_stats(session, user.id)
    history = await get_qc_history(session, user.id)

    if stats["total"] == 0:
        await message.answer(
            _("qc.history_empty", language=lang),
        )
        return

    text = (
        f"{_('qc.history_title', language=lang)}\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"  • {_('qc.stats_total', language=lang, count=stats['total'])}\n"
        f"  • {_('qc.stats_approved', language=lang, count=stats['approved'])}\n"
        f"  • {_('qc.stats_rejected', language=lang, count=stats['rejected'])}\n"
        f"  • {_('qc.stats_approve_rate', language=lang, rate=stats['approve_rate'])}\n\n"
        f"📋 <b>Oxirgi tekshirishlar:</b>"
    )

    await message.answer(
        text,
        reply_markup=qc_history_keyboard(history, lang),
    )


async def _edit_history(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
) -> None:
    """Tarixni tahrirlash."""
    lang = user.language or "uz"
    stats = await get_qc_full_stats(session, user.id)
    history = await get_qc_history(session, user.id)

    if stats["total"] == 0:
        try:
            await callback.message.edit_text(
                _("qc.history_empty", language=lang),
            )
        except Exception:
            await callback.message.answer(
                _("qc.history_empty", language=lang),
            )
        return

    text = (
        f"{_('qc.history_title', language=lang)}\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"  • {_('qc.stats_total', language=lang, count=stats['total'])}\n"
        f"  • {_('qc.stats_approved', language=lang, count=stats['approved'])}\n"
        f"  • {_('qc.stats_rejected', language=lang, count=stats['rejected'])}\n"
        f"  • {_('qc.stats_approve_rate', language=lang, rate=stats['approve_rate'])}\n\n"
        f"📋 <b>Oxirgi tekshirishlar:</b>"
    )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=qc_history_keyboard(history, lang),
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=qc_history_keyboard(history, lang),
        )
