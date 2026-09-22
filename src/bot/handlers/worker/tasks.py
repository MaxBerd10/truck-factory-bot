"""Ishchi — Mening vazifalarim."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsWorker
from src.bot.keyboards import (
    worker_task_detail_keyboard,
    worker_tasks_keyboard,
)
from src.database.models.user import User
from src.services.truck_step_service import (
    get_step_with_truck,
    get_worker_tasks,
)
from src.utils.constants import (
    PRIORITY_NAMES,
    STEP_NAMES,
)


router = Router(name="worker_tasks")


# ==== "Mening vazifalarim" ====
@router.message(IsWorker(), F.text == "📋 Vazifalarim")
async def show_tasks(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """Vazifalar ro'yxatini ko'rsatish."""
    await _send_tasks(message, user, session)


# ==== Yangilash ====
@router.callback_query(IsWorker(), F.data == "worker_refresh")
async def refresh_tasks(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Vazifalarni yangilash."""
    await callback.answer("🔄 Yangilanmoqda...")
    await _edit_tasks(callback, user, session)


# ==== Vazifa tafsiloti ====
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
        await callback.answer("❌ Vazifa topilmadi", show_alert=True)
        return

    await callback.answer()

    truck = step.truck
    priority_name = PRIORITY_NAMES.get(truck.priority, truck.priority)
    step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")

    status_map = {
        "pending": "⏳ Boshlash kerak",
        "rejected": "❌ Rad etilgan — qayta yuboring",
        "in_review": "🔍 QC tekshiruvida",
        "approved": "✅ Tasdiqlangan",
    }
    status_text = status_map.get(step.status, step.status)

    text = f"🚛 <b>{truck.serial_number}</b>\n\n"

    if truck.model:
        text += f"🏭 Model: {truck.model}\n"
    if truck.customer:
        text += f"👤 Buyurtmachi: {truck.customer}\n"
    if truck.deadline:
        text += f"📅 Muddat: {truck.deadline.strftime('%Y-%m-%d')}\n"

    text += (
        f"🎯 Prioritet: {priority_name}\n\n"
        f"🔧 Sizning stepingiz: <b>{step_name}</b>\n"
        f"📊 Holat: {status_text}\n"
    )

    if step.status == "rejected" and step.qc_comment:
        text += (
            f"\n❌ <b>Rad etish sababi:</b>\n"
            f"<i>{step.qc_comment}</i>\n"
        )

    if step.status == "in_review":
        text += (
            f"\n💡 <i>Sizning ishingiz QC tomonidan tekshirilmoqda. "
            f"Natijani kuting.</i>"
        )
    elif step.status == "approved":
        text += f"\n✅ <i>Bu ish tasdiqlangan. Rahmat!</i>"
    else:
        text += f"\n💡 <i>Ishni boshlash uchun quyidagi tugmani bosing.</i>"

    await callback.message.edit_text(
        text,
        reply_markup=worker_task_detail_keyboard(step),
    )


# ==== Yordamchi ====
async def _send_tasks(
    message: Message,
    user: User,
    session: AsyncSession,
) -> None:
    """Vazifalar ro'yxatini yuborish."""
    tasks = await get_worker_tasks(session, user.id)

    step_name = STEP_NAMES.get(user.step_number, f"Step {user.step_number}")

    if not tasks:
        await message.answer(
            f"✅ <b>Hammasi bajarilgan!</b>\n\n"
            f"🔧 Bo'lim: {step_name}\n\n"
            f"📋 Hozircha yangi vazifa yo'q.\n\n"
            f"💡 Yangi ish kelganda sizga xabar beramiz.",
        )
        return

    pending = sum(1 for t in tasks if t.status == "pending")
    rejected = sum(1 for t in tasks if t.status == "rejected")
    in_review = sum(1 for t in tasks if t.status == "in_review")

    text = (
        f"📋 <b>Mening vazifalarim</b>\n\n"
        f"🔧 Bo'lim: {step_name}\n\n"
        f"📊 Jami: <b>{len(tasks)}</b> ta\n"
    )

    if pending:
        text += f"⏳ Boshlash kerak: <b>{pending}</b>\n"
    if rejected:
        text += f"❌ Rad etilgan: <b>{rejected}</b>\n"
    if in_review:
        text += f"🔍 Tekshiruvda: <b>{in_review}</b>\n"

    text += "\n👇 Vazifani tanlang:"

    await message.answer(
        text,
        reply_markup=worker_tasks_keyboard(tasks),
    )


async def _edit_tasks(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
) -> None:
    """Vazifalar ro'yxatini tahrirlash."""
    tasks = await get_worker_tasks(session, user.id)

    step_name = STEP_NAMES.get(user.step_number, f"Step {user.step_number}")

    if not tasks:
        try:
            await callback.message.edit_text(
                f"✅ <b>Hammasi bajarilgan!</b>\n\n"
                f"🔧 Bo'lim: {step_name}\n\n"
                f"📋 Hozircha yangi vazifa yo'q.\n\n"
                f"💡 Yangi ish kelganda sizga xabar beramiz.",
            )
        except Exception:
            await callback.message.answer(
                f"✅ <b>Hammasi bajarilgan!</b>\n\n"
                f"🔧 Bo'lim: {step_name}\n\n"
                f"📋 Hozircha yangi vazifa yo'q.",
            )
        return

    pending = sum(1 for t in tasks if t.status == "pending")
    rejected = sum(1 for t in tasks if t.status == "rejected")
    in_review = sum(1 for t in tasks if t.status == "in_review")

    text = (
        f"📋 <b>Mening vazifalarim</b>\n\n"
        f"🔧 Bo'lim: {step_name}\n\n"
        f"📊 Jami: <b>{len(tasks)}</b> ta\n"
    )

    if pending:
        text += f"⏳ Boshlash kerak: <b>{pending}</b>\n"
    if rejected:
        text += f"❌ Rad etilgan: <b>{rejected}</b>\n"
    if in_review:
        text += f"🔍 Tekshiruvda: <b>{in_review}</b>\n"

    text += "\n👇 Vazifani tanlang:"

    try:
        await callback.message.edit_text(
            text,
            reply_markup=worker_tasks_keyboard(tasks),
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=worker_tasks_keyboard(tasks),
        )
