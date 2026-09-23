"""Ishchi — Tarixim."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsWorker, text_key
from src.bot.keyboards import (
    worker_history_detail_keyboard,
    worker_history_keyboard,
)
from src.database.models.user import User
from src.services.i18n_service import _, get_step_name
from src.services.stats_service import get_worker_full_stats
from src.services.truck_step_service import get_worker_history


router = Router(name="worker_history")


# ==================== "Tarixim" ====================
@router.message(IsWorker(), text_key("worker.menu_history"))
async def show_history(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """Ishchining tarixini ko'rsatish."""
    await _send_history(message, user, session)


# ==================== Yangilash ====================
@router.callback_query(IsWorker(), F.data == "worker_history")
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
@router.callback_query(IsWorker(), F.data.startswith("worker_history_view:"))
async def view_history_detail(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Tarix tafsilotini ko'rsatish."""
    from src.services.truck_step_service import get_step_with_truck

    step_id = int(callback.data.split(":")[1])
    step = await get_step_with_truck(session, step_id)

    if not step:
        await callback.answer(
            _("common.not_found", language=user.language or "uz"),
            show_alert=True,
        )
        return

    await callback.answer()

    lang = user.language or "uz"
    truck = step.truck
    step_name = get_step_name(step.step_number, lang)

    status_map = {
        "pending": "task_status_pending",
        "rejected": "task_status_rejected",
        "in_review": "task_status_in_review",
        "approved": "task_status_approved",
    }
    status_text = _(
        f"worker.{status_map.get(step.status, 'task_status_pending')}",
        language=lang,
    )

    text = f"🚛 <b>{truck.serial_number}</b>\n\n"
    text += f"🔧 <b>{step_name}</b>\n"
    text += f"📊 {status_text}\n"

    if step.worker_comment:
        text += f"\n📝 <b>Izoh:</b>\n<i>{step.worker_comment}</i>\n"

    if step.qc_comment:
        text += (
            f"\n❌ <b>{_('worker.task_rejected_reason', language=lang)}</b>\n"
            f"<i>{step.qc_comment}</i>\n"
        )

    if step.submitted_at:
        text += (
            f"\n🕐 {step.submitted_at.strftime('%Y-%m-%d %H:%M')}"
        )

    if step.media_type == "photo" and step.media_file_id:
        await callback.message.answer_photo(
            photo=step.media_file_id,
            caption=text,
            reply_markup=worker_history_detail_keyboard(step, lang),
        )
    elif step.media_type == "video" and step.media_file_id:
        await callback.message.answer_video(
            video=step.media_file_id,
            caption=text,
            reply_markup=worker_history_detail_keyboard(step, lang),
        )
    else:
        await callback.message.answer(
            text,
            reply_markup=worker_history_detail_keyboard(step, lang),
        )


# ==================== Yordamchi ====================
async def _send_history(
    message: Message,
    user: User,
    session: AsyncSession,
) -> None:
    """Tarixni yuborish."""
    lang = user.language or "uz"
    stats = await get_worker_full_stats(session, user.id)
    history = await get_worker_history(session, user.id)

    if stats["total"] == 0:
        await message.answer(
            _("worker.history_empty", language=lang),
        )
        return

    text = (
        f"{_('worker.history_title', language=lang)}\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"  • {_('worker.stats_jobs', language=lang, count=stats['total'])}\n"
        f"  • {_('worker.stats_approved', language=lang, count=stats['approved'])}\n"
        f"  • {_('worker.stats_in_review', language=lang, count=stats['in_review'])}\n"
        f"  • {_('worker.stats_rejected', language=lang, count=stats['rejected'])}\n"
        f"  • {_('worker.stats_success_rate', language=lang, rate=stats['success_rate'])}\n\n"
        f"📋 <b>Oxirgi ishlar:</b>"
    )

    await message.answer(
        text,
        reply_markup=worker_history_keyboard(history, lang),
    )


async def _edit_history(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
) -> None:
    """Tarixni tahrirlash."""
    lang = user.language or "uz"
    stats = await get_worker_full_stats(session, user.id)
    history = await get_worker_history(session, user.id)

    if stats["total"] == 0:
        try:
            await callback.message.edit_text(
                _("worker.history_empty", language=lang),
            )
        except Exception:
            await callback.message.answer(
                _("worker.history_empty", language=lang),
            )
        return

    text = (
        f"{_('worker.history_title', language=lang)}\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"  • {_('worker.stats_jobs', language=lang, count=stats['total'])}\n"
        f"  • {_('worker.stats_approved', language=lang, count=stats['approved'])}\n"
        f"  • {_('worker.stats_in_review', language=lang, count=stats['in_review'])}\n"
        f"  • {_('worker.stats_rejected', language=lang, count=stats['rejected'])}\n"
        f"  • {_('worker.stats_success_rate', language=lang, rate=stats['success_rate'])}\n\n"
        f"📋 <b>Oxirgi ishlar:</b>"
    )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=worker_history_keyboard(history, lang),
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=worker_history_keyboard(history, lang),
        )
