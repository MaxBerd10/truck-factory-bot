"""QC — Tarixim."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsQC
from src.bot.keyboards import (
    qc_history_detail_keyboard,
    qc_history_keyboard,
)
from src.database.models.user import User
from src.services.qc_service import get_qc_history
from src.services.stats_service import get_qc_full_stats
from src.services.qc_service import get_step_for_review
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

    if step.media_type == "photo" and step.media_file_id:
        await callback.message.answer_photo(
            photo=step.media_file_id,
            caption=text,
            reply_markup=qc_history_detail_keyboard(),
        )
    else:
        await callback.message.answer(
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
    stats = await get_qc_full_stats(session, user.id)
    history = await get_qc_history(session, user.id)

    if stats["total"] == 0:
        await message.answer(
            "📜 <b>Tarixim</b>\n\n"
            "Hozircha tarix bo'sh.\n\n"
            "<i>Ishlarni tekshirganingizdan keyin bu yerda ko'rinadi.</i>",
        )
        return

    text = (
        f"📜 <b>Tarixim</b>\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"  • Jami tekshirilgan: <b>{stats['total']}</b>\n"
        f"  • ✅ Tasdiqlangan: <b>{stats['approved']}</b>\n"
        f"  • ❌ Rad etilgan: <b>{stats['rejected']}</b>\n"
        f"  • 📈 Tasdiqlash foizi: <b>{stats['approve_rate']}%</b>\n\n"
        f"📋 <b>Oxirgi tekshirishlar:</b>"
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
    stats = await get_qc_full_stats(session, user.id)
    history = await get_qc_history(session, user.id)

    if stats["total"] == 0:
        try:
            await callback.message.edit_text(
                "📜 <b>Tarixim</b>\n\n"
                "Hozircha tarix bo'sh.",
            )
        except Exception:
            await callback.message.answer(
                "📜 <b>Tarixim</b>\n\n"
                "Hozircha tarix bo'sh.",
            )
        return

    text = (
        f"📜 <b>Tarixim</b>\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"  • Jami tekshirilgan: <b>{stats['total']}</b>\n"
        f"  • ✅ Tasdiqlangan: <b>{stats['approved']}</b>\n"
        f"  • ❌ Rad etilgan: <b>{stats['rejected']}</b>\n"
        f"  • 📈 Tasdiqlash foizi: <b>{stats['approve_rate']}%</b>\n\n"
        f"📋 <b>Oxirgi tekshirishlar:</b>"
    )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=qc_history_keyboard(history),
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=qc_history_keyboard(history),
        )
