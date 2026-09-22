"""QC — Ishni tekshirish (approve/reject)."""
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsQC
from src.bot.keyboards import (
    qc_approve_confirm_keyboard,
    qc_queue_keyboard,
    qc_reject_cancel_keyboard,
    qc_reject_confirm_keyboard,
    qc_review_keyboard,
)
from src.bot.states import RejectStepFSM
from src.database.models.user import User
from src.services.qc_service import (
    approve_step,
    get_qc_queue,
    get_step_for_review,
    reject_step,
)
from src.utils.constants import (
    PRIORITY_NAMES,
    STEP_NAMES,
)
from src.utils.logger import logger


router = Router(name="qc_review")


# ==== Ishni ko'rish ====
@router.callback_query(IsQC(), F.data.startswith("qc_view:"))
async def view_for_review(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    """Ishni tekshirish uchun ko'rish."""
    await state.clear()

    step_id = int(callback.data.split(":")[1])
    step = await get_step_for_review(session, step_id)

    if not step:
        await callback.answer("❌ Ish topilmadi", show_alert=True)
        return

    if step.status != "in_review":
        await callback.answer(
            "⚠️ Bu ish allaqachon tekshirilgan",
            show_alert=True,
        )
        return

    await callback.answer()
    await _send_review(callback, step)


# ==== Approve — confirm ====
@router.callback_query(IsQC(), F.data.startswith("qc_approve:"))
async def ask_approve(
    callback: CallbackQuery,
    session: AsyncSession,
):
    """Tasdiqlashni so'rash."""
    step_id = int(callback.data.split(":")[1])
    step = await get_step_for_review(session, step_id)

    if not step or step.status != "in_review":
        await callback.answer("❌ Xato", show_alert=True)
        return

    await callback.answer()

    text = (
        f"✅ <b>Tasdiqlash</b>\n\n"
        f"🚛 Truck: <b>{step.truck.serial_number}</b>\n"
        f"🔧 Step: <b>{STEP_NAMES.get(step.step_number, step.step_number)}</b>\n\n"
        f"<b>Ishni tasdiqlaysizmi?</b>\n\n"
    )

    if step.step_number < 6:
        text += "<i>Shundan keyin truck keyingi stepga o'tadi.</i>"
    else:
        text += "<i>Bu oxirgi step — truck TAYYOR bo'ladi!</i>"

    await callback.message.answer(
        text,
        reply_markup=qc_approve_confirm_keyboard(step_id),
    )


# ==== Approve — confirm ====
@router.callback_query(IsQC(), F.data.startswith("qc_approve_confirm:"))
async def confirm_approve(
    callback: CallbackQuery,
    session: AsyncSession,
    user: User,
    bot: Bot,
):
    """Tasdiqlashni amalga oshirish."""
    step_id = int(callback.data.split(":")[1])
    step = await get_step_for_review(session, step_id)

    if not step or step.status != "in_review":
        await callback.answer("❌ Xato", show_alert=True)
        return

    # Tasdiqlash + bildirishnoma
    truck = await approve_step(session, step, qc_id=user.id, bot=bot)

    await callback.answer("✅ Tasdiqlandi", show_alert=False)

    step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")

    if truck.is_completed:
        text = (
            f"🎉 <b>TRUCK TAYYOR!</b>\n\n"
            f"🚛 <b>{truck.serial_number}</b>\n"
            f"🏭 {truck.model or '—'}\n"
            f"👤 {truck.customer or '—'}\n\n"
            f"✅ Barcha 6 ta step tasdiqlandi!"
        )
    else:
        next_step_name = STEP_NAMES.get(
            truck.current_step, f"Step {truck.current_step}"
        )
        text = (
            f"✅ <b>Tasdiqlandi!</b>\n\n"
            f"🚛 {truck.serial_number}\n"
            f"🔧 {step_name} ✅\n\n"
            f"📍 Keyingi step: <b>{next_step_name}</b>\n\n"
            f"<i>Endi keyingi step ishchisi ishlashi mumkin.</i>"
        )

    await callback.message.answer(text)


# ==== Reject — sabab so'rash ====
@router.callback_query(IsQC(), F.data.startswith("qc_reject:"))
async def ask_reject(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    """Rad etish sababini so'rash."""
    step_id = int(callback.data.split(":")[1])
    step = await get_step_for_review(session, step_id)

    if not step or step.status != "in_review":
        await callback.answer("❌ Xato", show_alert=True)
        return

    await callback.answer()

    await state.clear()
    await state.update_data(step_id=step_id)
    await state.set_state(RejectStepFSM.reason)

    await callback.message.answer(
        f"❌ <b>Rad etish</b>\n\n"
        f"🚛 Truck: <b>{step.truck.serial_number}</b>\n"
        f"🔧 Step: <b>{STEP_NAMES.get(step.step_number, step.step_number)}</b>\n\n"
        f"📝 <b>Rad etish sababini yozing:</b>\n\n"
        f"<i>Masalan: Rasm sifati past, qayta yuboring</i>",
        reply_markup=qc_reject_cancel_keyboard(),
    )


# ==== Reject — sabab qabul qilish ====
@router.message(RejectStepFSM.reason, F.text)
async def process_reject_reason(
    message: Message,
    state: FSMContext,
):
    """Rad etish sababini qabul qilish."""
    text = message.text.strip()

    if len(text) < 5:
        await message.answer(
            "❌ <b>Juda qisqa!</b>\n\n"
            "Sabab kamida 5 belgidan iborat bo'lishi kerak.\n"
            "Qaytadan kiriting:",
            reply_markup=qc_reject_cancel_keyboard(),
        )
        return

    if len(text) > 500:
        await message.answer(
            "❌ <b>Juda uzun!</b>\n\n"
            "Sabab 500 belgidan oshmasligi kerak.\n"
            "Qaytadan kiriting:",
            reply_markup=qc_reject_cancel_keyboard(),
        )
        return

    await state.update_data(reason=text)
    data = await state.get_data()
    step_id = data["step_id"]

    await message.answer(
        f"❌ <b>Rad etishni tasdiqlang</b>\n\n"
        f"📝 Sabab: <i>{text}</i>\n\n"
        f"<b>Rostdan ham rad etmoqchimisiz?</b>",
        reply_markup=qc_reject_confirm_keyboard(step_id),
    )


# ==== Reject — confirm ====
@router.callback_query(IsQC(), F.data.startswith("qc_reject_confirm:"))
async def confirm_reject(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User,
    bot: Bot,
):
    """Rad etishni amalga oshirish."""
    step_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    reason = data.get("reason")

    if not reason:
        await callback.answer("❌ Sabab yo'q", show_alert=True)
        return

    step = await get_step_for_review(session, step_id)

    if not step or step.status != "in_review":
        await callback.answer("❌ Xato", show_alert=True)
        return

    # Rad etish + bildirishnoma
    await reject_step(session, step, qc_id=user.id, reason=reason, bot=bot)

    await state.clear()
    await callback.answer("❌ Rad etildi", show_alert=False)

    step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")

    text = (
        f"❌ <b>Rad etildi</b>\n\n"
        f"🚛 Truck: <b>{step.truck.serial_number}</b>\n"
        f"🔧 Step: <b>{step_name}</b>\n\n"
        f"📝 Sabab: <i>{reason}</i>\n\n"
        f"<i>Ishchiga xabar yuborildi, qayta yuborishi mumkin.</i>"
    )

    await callback.message.answer(text)


# ==== Reject — restart ====
@router.callback_query(IsQC(), F.data.startswith("qc_reject_restart:"))
async def restart_reject(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Sababni qayta kiritish."""
    step_id = int(callback.data.split(":")[1])
    await callback.answer()

    await state.clear()
    await state.update_data(step_id=step_id)
    await state.set_state(RejectStepFSM.reason)

    await callback.message.answer(
        "📝 <b>Rad etish sababini yozing:</b>",
        reply_markup=qc_reject_cancel_keyboard(),
    )


# ==== Reject — bekor qilish ====
@router.callback_query(F.data == "qc_reject_cancel")
async def cancel_reject(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    """Rad etishni bekor qilish."""
    await callback.answer("❌ Bekor qilindi")

    data = await state.get_data()
    step_id = data.get("step_id")
    await state.clear()

    if step_id:
        step = await get_step_for_review(session, step_id)
        if step and step.status == "in_review":
            steps = await get_qc_queue(session)

            if not steps:
                await callback.message.answer(
                    "🔔 <b>Tekshirish navbati</b>\n\n"
                    "✅ Navbat bo'sh."
                )
                return

            await callback.message.answer(
                f"🔔 <b>Tekshirish navbati</b>\n\n"
                f"📊 Jami: <b>{len(steps)}</b> ta ish",
                reply_markup=qc_queue_keyboard(steps),
            )
            return

    steps = await get_qc_queue(session)

    if not steps:
        await callback.message.answer(
            "🔔 <b>Tekshirish navbati</b>\n\n"
            "✅ Navbat bo'sh."
        )
        return

    await callback.message.answer(
        f"🔔 <b>Tekshirish navbati</b>\n\n"
        f"📊 Jami: <b>{len(steps)}</b> ta ish",
        reply_markup=qc_queue_keyboard(steps),
    )


# ==== Yordamchi ====
async def _send_review(callback: CallbackQuery, step) -> None:
    """Ishni ko'rsatish."""
    truck = step.truck
    worker = step.worker

    priority_name = PRIORITY_NAMES.get(truck.priority, truck.priority)
    step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")

    text = (
        f"🔍 <b>Tekshirish</b>\n\n"
        f"🚛 Truck: <b>{truck.serial_number}</b>\n"
    )

    if truck.model:
        text += f"🏭 Model: {truck.model}\n"
    if truck.customer:
        text += f"👤 Buyurtmachi: {truck.customer}\n"
    if truck.deadline:
        text += f"📅 Muddat: {truck.deadline.strftime('%Y-%m-%d')}\n"

    text += f"🎯 Prioritet: {priority_name}\n\n"

    text += f"🔧 Step: <b>{step_name}</b>\n"

    if worker:
        text += f"👷 Ishchi: {worker.full_name}\n"

    if step.submitted_at:
        text += (
            f"🕐 Yuborilgan: "
            f"{step.submitted_at.strftime('%Y-%m-%d %H:%M')}\n"
        )

    if step.worker_comment:
        text += f"\n📝 <b>Izoh:</b>\n<i>{step.worker_comment}</i>\n"

    text += f"\n📊 <b>Qarorni tanlang:</b>"

    if step.media_type == "photo" and step.media_file_id:
        await callback.message.answer_photo(
            photo=step.media_file_id,
            caption=text,
            reply_markup=qc_review_keyboard(step.id),
        )
    elif step.media_type == "video" and step.media_file_id:
        await callback.message.answer_video(
            video=step.media_file_id,
            caption=text,
            reply_markup=qc_review_keyboard(step.id),
        )
    elif step.media_type == "document" and step.media_file_id:
        await callback.message.answer_document(
            document=step.media_file_id,
            caption=text,
            reply_markup=qc_review_keyboard(step.id),
        )
    else:
        await callback.message.answer(
            text,
            reply_markup=qc_review_keyboard(step.id),
        )
