"""QC — Tarixim."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsQC
from src.bot.keyboards import (
    qc_history_detail_keyboard,
    qc_history_keyboard,
    qc_review_keyboard,
)
from src.database.models.user import User
from src.services.qc_service import get_qc_history, get_step_for_review
from src.utils.constants import (
    PRIORITY_NAMES,
    STEP_NAMES,
)


router = Router(name="qc_history")


# ==== "Tarixim" ====
@router.message(IsQC(), F.text == "📜 Tarixim")
async def show_history(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """QC tarixini ko'rsatish."""
    await _send_history(message, user, session)


# ==== Yangilash ====
@router.callback_query(IsQC(), F.data == "qc_history")
async def refresh_history(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Tarixni yangilash."""
    await callback.answer()
    await _edit_history(callback, user, session)


# ==== Tarix tafsiloti ====
@router.callback_query(IsQC(), F.data.startswith("qc_history_view:"))
async def view_history_detail(
    callback: CallbackQuery,
    session: AsyncSession,
):
    """Tarix tafsilotini ko'rish."""
    step_id = int(callback.data.split(":")[1])
    step = await get_step_for_review(session, step_id)

    if not step:
        await callback.answer("❌ Topilmadi", show_alert=True)
        return

    await callback.answer()

    truck = step.truck
    priority_name = PRIORITY_NAMES.get(truck.priority, truck.priority)
    step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")

    # Status
    if step.is_approved:
        status_text = "✅ Tasdiqlangan"
    elif step.is_rejected:
        status_text = "❌ Rad etilgan"
    else:
        status_text = "🔍 Tekshirilmoqda"

    text = (
        f"📜 <b>Tarix tafsiloti</b>\n\n"
        f"🚛 Truck: <b>{truck.serial_number}</b>\n"
        f"🔧 Step: <b>{step_name}</b>\n"
        f"🎯 Prioritet: {priority_name}\n\n"
        f"📊 Holat: {status_text}\n"
    )

    if step.worker:
        text += f"👷 Ishchi: {step.worker.full_name}\n"

    if step.worker_comment:
        text += f"\n📝 <b>Ishchi izohi:</b>\n<i>{step.worker_comment}</i>\n"

    if step.qc_comment:
        text += f"\n❌ <b>Rad etish sababi:</b>\n<i>{step.qc_comment}</i>\n"

    if step.reviewed_at:
        text += (
            f"\n🕐 Tekshirilgan: "
            f"{step.reviewed_at.strftime('%Y-%m-%d %H:%M')}"
        )

    # Media
    if step.media_type == "photo" and step.media_file_id:
        await callback.message.answer_photo(
            photo=step.media_file_id,
            caption=text,
            reply_markup=qc_history_detail_keyboard(),
        )
        await callback.message.delete()
    else:
        await callback.message.edit_text(
            text,
            reply_markup=qc_history_detail_keyboard(),
        )


# ==== Yordamchi ====
async def _send_history(
    message: Message,
    user: User,
    session: AsyncSession,
) -> None:
    """Tarixni yuborish."""
    history = await get_qc_history(session, user.id)

    if not history:
        await message.answer(
            "📜 <b>Tarixim</b>\n\n"
            "Hozircha tarix bo'sh.\n\n"
            "<i>Ishlarni tekshirganingizdan keyin bu yerda ko'rinadi.</i>",
        )
        return

    # Statistika
    approved = sum(1 for h in history if h.is_approved)
    rejected = sum(1 for h in history if h.is_rejected)

    text = (
        f"📜 <b>Tarixim</b>\n\n"
        f"📊 Jami: <b>{len(history)}</b> ta\n"
        f"✅ Tasdiqlangan: {approved}\n"
        f"❌ Rad etilgan: {rejected}\n\n"
        f"Batafsil ko'rish uchun tanlang:"
    )

    await message.answer(
        text,
        reply_markup=qc_history_keyboard(history),
    )


async def _edit_history(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
) -> None:
    """Tarixni tahrirlash."""
    history = await get_qc_history(session, user.id)

    if not history:
        await callback.message.edit_text(
            "📜 <b>Tarixim</b>\n\n"
            "Hozircha tarix bo'sh.",
        )
        return

    approved = sum(1 for h in history if h.is_approved)
    rejected = sum(1 for h in history if h.is_rejected)

    text = (
        f"📜 <b>Tarixim</b>\n\n"
        f"📊 Jami: <b>{len(history)}</b> ta\n"
        f"✅ Tasdiqlangan: {approved}\n"
        f"❌ Rad etilgan: {rejected}\n\n"
        f"Batafsil ko'rish uchun tanlang:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=qc_history_keyboard(history),
    )
