"""Ishchi — Mening vazifalarim."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsWorker, text_key
from src.bot.keyboards import (
    worker_task_detail_keyboard,
    worker_tasks_keyboard,
)
from src.database.models.user import User
from src.services.i18n_service import (
    _,
    get_priority_name,
    get_step_name,
)
from src.services.truck_step_service import (
    get_step_with_truck,
    get_worker_tasks,
)


router = Router(name="worker_tasks")


# ==================== "Mening vazifalarim" ====================
@router.message(IsWorker(), text_key("worker.menu_tasks"))
async def show_tasks(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """Vazifalar ro'yxatini ko'rsatish."""
    await _send_tasks(message, user, session)


# ==================== Yangilash ====================
@router.callback_query(IsWorker(), F.data == "worker_refresh")
async def refresh_tasks(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Vazifalarni yangilash."""
    lang = user.language or "uz"
    await callback.answer(_("common.loading", language=lang))
    await _edit_tasks(callback, user, session)


# ==================== Vazifa tafsiloti ====================
@router.callback_query(IsWorker(), F.data.startswith("worker_task:"))
async def view_task_detail(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Vazifa tafsilotini ko'rsatish."""
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
    priority_name = get_priority_name(truck.priority, lang)
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

    if truck.model:
        text += f"🏭 {truck.model}\n"
    if truck.customer:
        text += f"👤 {truck.customer}\n"
    if truck.deadline:
        text += f"📅 {truck.deadline.strftime('%Y-%m-%d')}\n"

    text += f"\n🔧 <b>{step_name}</b>\n"
    text += f"📊 {priority_name} | {status_text}\n"

    if step.status == "rejected" and step.qc_comment:
        text += (
            f"\n❌ <b>{_('worker.task_rejected_reason', language=lang)}</b>\n"
            f"<i>{step.qc_comment}</i>\n"
        )

    if step.status == "in_review":
        text += f"\n💡 <i>{_('worker.task_wait_qc', language=lang)}</i>"
    elif step.status == "approved":
        text += f"\n✅ <i>{_('worker.task_approved_msg', language=lang)}</i>"
    else:
        text += f"\n💡 <i>{_('worker.task_start_prompt', language=lang)}</i>"

    await callback.message.edit_text(
        text,
        reply_markup=worker_task_detail_keyboard(step, lang),
    )


# ==================== Yordamchi ====================
async def _send_tasks(
    message: Message,
    user: User,
    session: AsyncSession,
) -> None:
    """Vazifalar ro'yxatini yuborish."""
    lang = user.language or "uz"
    tasks = await get_worker_tasks(session, user.id, user.step_number)
    step_name = (
        get_step_name(user.step_number, lang) if user.step_number else "—"
    )

    if not tasks:
        await message.answer(
            _("worker.tasks_empty", language=lang, step=step_name),
        )
        return

    pending = sum(1 for t in tasks if t.status == "pending")
    rejected = sum(1 for t in tasks if t.status == "rejected")
    in_review = sum(1 for t in tasks if t.status == "in_review")

    text = f"📋 <b>{_('worker.tasks_title', language=lang)}</b>\n\n"
    text += f"🔧 {step_name}\n\n"
    text += f"{_('worker.tasks_total', language=lang, count=len(tasks))}\n"

    if pending:
        text += f"{_('worker.tasks_pending', language=lang, count=pending)}\n"
    if rejected:
        text += f"{_('worker.tasks_rejected', language=lang, count=rejected)}\n"
    if in_review:
        text += f"{_('worker.tasks_in_review', language=lang, count=in_review)}\n"

    text += f"\n{_('worker.tasks_choose', language=lang)}"

    await message.answer(
        text,
        reply_markup=worker_tasks_keyboard(tasks, lang),
    )


async def _edit_tasks(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
) -> None:
    """Vazifalar ro'yxatini tahrirlash."""
    lang = user.language or "uz"
    tasks = await get_worker_tasks(session, user.id, user.step_number)
    step_name = (
        get_step_name(user.step_number, lang) if user.step_number else "—"
    )

    if not tasks:
        try:
            await callback.message.edit_text(
                _("worker.tasks_empty", language=lang, step=step_name),
            )
        except Exception:
            await callback.message.answer(
                _("worker.tasks_empty", language=lang, step=step_name),
            )
        return

    pending = sum(1 for t in tasks if t.status == "pending")
    rejected = sum(1 for t in tasks if t.status == "rejected")
    in_review = sum(1 for t in tasks if t.status == "in_review")

    text = f"📋 <b>{_('worker.tasks_title', language=lang)}</b>\n\n"
    text += f"🔧 {step_name}\n\n"
    text += f"{_('worker.tasks_total', language=lang, count=len(tasks))}\n"

    if pending:
        text += f"{_('worker.tasks_pending', language=lang, count=pending)}\n"
    if rejected:
        text += f"{_('worker.tasks_rejected', language=lang, count=rejected)}\n"
    if in_review:
        text += f"{_('worker.tasks_in_review', language=lang, count=in_review)}\n"

    text += f"\n{_('worker.tasks_choose', language=lang)}"

    try:
        await callback.message.edit_text(
            text,
            reply_markup=worker_tasks_keyboard(tasks, lang),
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=worker_tasks_keyboard(tasks, lang),
        )
