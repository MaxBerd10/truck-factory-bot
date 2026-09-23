"""QC — Ishni tekshirish (approve/reject)."""
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsQC
from src.bot.keyboards import (
    qc_after_action_keyboard,
    qc_approve_confirm_keyboard,
    qc_queue_keyboard,
    qc_reject_cancel_keyboard,
    qc_reject_confirm_keyboard,
    qc_review_keyboard,
)
from src.bot.states import RejectStepFSM
from src.database.models.user import User
from src.services.i18n_service import _, get_step_name
from src.services.qc_service import (
    approve_step,
    get_qc_queue,
    get_step_for_review,
    reject_step,
)


router = Router(name="qc_review")


# ==================== Ishni ko'rish ====================
@router.callback_query(IsQC(), F.data.startswith("qc_view:"))
async def view_for_review(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    session: AsyncSession,
):
    """Ishni tekshirish uchun ko'rish."""
    await state.clear()
    lang = user.language or "uz"

    step_id = int(callback.data.split(":")[1])
    step = await get_step_for_review(session, step_id)

    if not step:
        await callback.answer(
            _("common.not_found", language=lang),
            show_alert=True,
        )
        return

    if step.status != "in_review":
        await callback.answer(
            _("qc.already_reviewed", language=lang),
            show_alert=True,
        )
        return

    await callback.answer()
    await _send_review(callback, step, lang)


# ==================== Approve — confirm ====================
@router.callback_query(IsQC(), F.data.startswith("qc_approve:"))
async def ask_approve(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Tasdiqlashni so'rash."""
    lang = user.language or "uz"
    step_id = int(callback.data.split(":")[1])
    step = await get_step_for_review(session, step_id)

    if not step or step.status != "in_review":
        await callback.answer(
            _("qc.already_reviewed", language=lang),
            show_alert=True,
        )
        return

    await callback.answer()

    step_name = get_step_name(step.step_number, lang)

    text = (
        f"{_('qc.approve_title', language=lang)}\n\n"
        f"🚛 <b>{step.truck.serial_number}</b>\n"
        f"🔧 <b>{step_name}</b>\n\n"
        f"<b>{_('qc.approve_question', language=lang)}</b>\n\n"
    )

    if step.step_number < 6:
        text += f"<i>{_('qc.approve_next_step', language=lang)}</i>"
    else:
        text += f"<i>{_('qc.approve_last_step', language=lang)}</i>"

    await callback.message.answer(
        text,
        reply_markup=qc_approve_confirm_keyboard(step_id, lang),
    )


# ==================== Approve — confirm ====================
@router.callback_query(IsQC(), F.data.startswith("qc_approve_confirm:"))
async def confirm_approve(
    callback: CallbackQuery,
    session: AsyncSession,
    user: User,
    bot: Bot,
):
    """Tasdiqlashni amalga oshirish."""
    lang = user.language or "uz"
    step_id = int(callback.data.split(":")[1])
    step = await get_step_for_review(session, step_id)

    if not step or step.status != "in_review":
        await callback.answer(
            _("common.error_generic", language=lang),
            show_alert=True,
        )
        return

    truck = await approve_step(session, step, qc_id=user.id, bot=bot)

    await callback.answer(
        _("qc.approve_success_alert", language=lang),
        show_alert=False,
    )

    step_name = get_step_name(step.step_number, lang)

    if truck.is_completed:
        text = _(
            "qc.approve_truck_ready",
            language=lang,
            truck=truck.serial_number,
            model=truck.model or "—",
            customer=truck.customer or "—",
        )
    else:
        next_step_name = get_step_name(truck.current_step, lang)
        text = _(
            "qc.approve_success",
            language=lang,
            truck=truck.serial_number,
            step=step_name,
            next_step=next_step_name,
        )

    await callback.message.answer(
        text,
        reply_markup=qc_after_action_keyboard(lang),
    )


# ==================== Reject — sabab so'rash ====================
@router.callback_query(IsQC(), F.data.startswith("qc_reject:"))
async def ask_reject(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    session: AsyncSession,
):
    """Rad etish sababini so'rash."""
    lang = user.language or "uz"
    step_id = int(callback.data.split(":")[1])
    step = await get_step_for_review(session, step_id)

    if not step or step.status != "in_review":
        await callback.answer(
            _("qc.already_reviewed", language=lang),
            show_alert=True,
        )
        return

    await callback.answer()

    await state.clear()
    await state.update_data(step_id=step_id)
    await state.set_state(RejectStepFSM.reason)

    step_name = get_step_name(step.step_number, lang)

    await callback.message.answer(
        f"{_('qc.reject_title', language=lang)}\n\n"
        f"🚛 <b>{step.truck.serial_number}</b>\n"
        f"🔧 <b>{step_name}</b>\n\n"
        f"{_('qc.reject_prompt', language=lang)}",
        reply_markup=qc_reject_cancel_keyboard(lang),
    )


# ==================== Reject — sabab qabul qilish ====================
@router.message(RejectStepFSM.reason, F.text)
async def process_reject_reason(
    message: Message,
    state: FSMContext,
    user: User,
):
    """Rad etish sababini qabul qilish."""
    lang = user.language or "uz"
    text = message.text.strip()

    if len(text) < 5:
        await message.answer(
            _("qc.reject_too_short", language=lang, len=len(text)),
            reply_markup=qc_reject_cancel_keyboard(lang),
        )
        return

    if len(text) > 500:
        await message.answer(
            _("qc.reject_too_long", language=lang, len=len(text)),
            reply_markup=qc_reject_cancel_keyboard(lang),
        )
        return

    await state.update_data(reason=text)
    data = await state.get_data()
    step_id = data["step_id"]

    await message.answer(
        _("qc.reject_confirm", language=lang, reason=text),
        reply_markup=qc_reject_confirm_keyboard(step_id, lang),
    )


# ==================== Reject — confirm ====================
@router.callback_query(IsQC(), F.data.startswith("qc_reject_confirm:"))
async def confirm_reject(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User,
    bot: Bot,
):
    """Rad etishni amalga oshirish."""
    lang = user.language or "uz"
    step_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    reason = data.get("reason")

    if not reason:
        await callback.answer(
            _("common.error_generic", language=lang),
            show_alert=True,
        )
        return

    step = await get_step_for_review(session, step_id)

    if not step or step.status != "in_review":
        await callback.answer(
            _("common.error_generic", language=lang),
            show_alert=True,
        )
        return

    await reject_step(session, step, qc_id=user.id, reason=reason, bot=bot)

    await state.clear()
    await callback.answer(
        _("qc.reject_success_alert", language=lang),
        show_alert=False,
    )

    step_name = get_step_name(step.step_number, lang)

    text = _(
        "qc.reject_success",
        language=lang,
        truck=step.truck.serial_number,
        step=step_name,
        reason=reason,
    )

    await callback.message.answer(
        text,
        reply_markup=qc_after_action_keyboard(lang),
    )


# ==================== Reject — restart ====================
@router.callback_query(IsQC(), F.data.startswith("qc_reject_restart:"))
async def restart_reject(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Sababni qayta kiritish."""
    lang = user.language or "uz"
    step_id = int(callback.data.split(":")[1])
    await callback.answer()

    await state.clear()
    await state.update_data(step_id=step_id)
    await state.set_state(RejectStepFSM.reason)

    await callback.message.answer(
        _("qc.reject_prompt", language=lang),
        reply_markup=qc_reject_cancel_keyboard(lang),
    )


# ==================== Reject — bekor qilish ====================
@router.callback_query(F.data == "qc_reject_cancel")
async def cancel_reject(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    session: AsyncSession,
):
    """Rad etishni bekor qilish."""
    lang = user.language or "uz"
    await callback.answer(_("common.cancel", language=lang))
    await state.clear()

    steps = await get_qc_queue(session)

    if not steps:
        await callback.message.answer(
            _("qc.queue_empty", language=lang),
            reply_markup=qc_after_action_keyboard(lang),
        )
        return

    await callback.message.answer(
        f"{_('qc.queue_title', language=lang)}\n\n"
        f"{_('qc.queue_total', language=lang, count=len(steps))}\n\n"
        f"{_('qc.queue_choose', language=lang)}",
        reply_markup=qc_queue_keyboard(steps, lang),
    )


# ==================== Yordamchi ====================
async def _send_review(
    callback: CallbackQuery,
    step,
    lang: str,
) -> None:
    """Ishni ko'rsatish."""
    truck = step.truck
    worker = step.worker

    from src.services.i18n_service import get_priority_name

    priority_name = get_priority_name(truck.priority, lang)
    step_name = get_step_name(step.step_number, lang)

    text = f"{_('qc.review_title', language=lang)}\n\n"
    text += f"🚛 <b>{truck.serial_number}</b>\n"

    if truck.model:
        text += f"🏭 {truck.model}\n"
    if truck.customer:
        text += f"👤 {truck.customer}\n"
    if truck.deadline:
        text += f"📅 {truck.deadline.strftime('%Y-%m-%d')}\n"

    text += f"🎯 {priority_name}\n\n"
    text += f"🔧 <b>{step_name}</b>\n"

    if worker:
        text += f"👷 {worker.full_name}\n"

    if step.submitted_at:
        text += f"🕐 {step.submitted_at.strftime('%Y-%m-%d %H:%M')}\n"

    if step.worker_comment:
        text += f"\n📝 <b>Izoh:</b>\n<i>{step.worker_comment}</i>\n"

    text += f"\n{_('qc.review_choose_decision', language=lang)}"

    keyboard = qc_review_keyboard(step.id, lang)

    if step.media_type == "photo" and step.media_file_id:
        await callback.message.answer_photo(
            photo=step.media_file_id,
            caption=text,
            reply_markup=keyboard,
        )
    elif step.media_type == "video" and step.media_file_id:
        await callback.message.answer_video(
            video=step.media_file_id,
            caption=text,
            reply_markup=keyboard,
        )
    elif step.media_type == "document" and step.media_file_id:
        await callback.message.answer_document(
            document=step.media_file_id,
            caption=text,
            reply_markup=keyboard,
        )
    else:
        await callback.message.answer(
            text,
            reply_markup=keyboard,
        )
