"""Admin — Truck timeline (tarix)."""
from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.bot.filters import IsAdmin
from src.bot.keyboards.truck import truck_detail_keyboard
from src.database.models.truck_step import TruckStep
from src.utils.constants import STEP_NAMES


router = Router(name="admin_truck_timeline")


@router.callback_query(IsAdmin(), F.data.startswith("truck_timeline:"))
async def show_timeline(
    callback: CallbackQuery,
    session: AsyncSession,
):
    """Truck tarixini ko'rsatish."""
    truck_id = int(callback.data.split(":")[1])

    stmt = (
        select(TruckStep)
        .where(TruckStep.truck_id == truck_id)
        .options(
            selectinload(TruckStep.worker),
            selectinload(TruckStep.qc),
            selectinload(TruckStep.truck),
        )
        .order_by(TruckStep.step_number)
    )
    result = await session.execute(stmt)
    steps = list(result.scalars().all())

    if not steps:
        await callback.answer("❌ Ma'lumot topilmadi", show_alert=True)
        return

    await callback.answer()

    truck = steps[0].truck

    text = (
        f"📅 <b>Truck tarixi</b>\n\n"
        f"🚛 <b>{truck.serial_number}</b>\n"
    )

    if truck.model:
        text += f"🏭 {truck.model}\n"
    if truck.customer:
        text += f"👤 {truck.customer}\n"

    text += "\n━━━━━━━━━━━━━━━━━━\n\n"

    for step in steps:
        step_name = STEP_NAMES.get(
            step.step_number, f"Step {step.step_number}"
        )

        status_icon = {
            "pending": "⏳",
            "in_review": "🔍",
            "approved": "✅",
            "rejected": "❌",
        }.get(step.status, "⚪")

        text += f"{status_icon} <b>{step.step_number}. {step_name}</b>\n"

        if step.worker:
            text += f"   👷 {step.worker.full_name}\n"

        if step.submitted_at:
            text += f"   📤 {step.submitted_at.strftime('%m-%d %H:%M')}\n"

        if step.reviewed_at:
            text += f"   ✅ {step.reviewed_at.strftime('%m-%d %H:%M')}\n"

        if step.qc_comment:
            comment = step.qc_comment[:50]
            if len(step.qc_comment) > 50:
                comment += "..."
            text += f"   📝 <i>{comment}</i>\n"

        text += "\n"

    # Umumiy davomiylik
    if truck.completed_at and truck.created_at:
        duration = truck.completed_at - truck.created_at
        days = duration.days
        hours = duration.seconds // 3600

        if days > 0:
            text += f"⏱ <b>Umumiy davomiylik:</b> {days} kun {hours} soat\n"
        else:
            text += f"⏱ <b>Umumiy davomiylik:</b> {hours} soat\n"

    if truck.completed_at:
        text += (
            f"🏁 <b>Tugatilgan:</b> "
            f"{truck.completed_at.strftime('%Y-%m-%d %H:%M')}\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=truck_detail_keyboard(truck),
    )
