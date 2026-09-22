"""Ishchi — Mening vazifalarim."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsWorker
from src.bot.keyboards import (
    worker_task_detail_keyboard,
    worker_tasks_keyboard,
)
from src.database.models.truck_step import TruckStep
from src.database.models.user import User
from src.services.truck_step_service import (
    claim_step,
    get_step_with_truck,
    get_worker_tasks,
)
from src.utils.constants import (
    PRIORITY_NAMES,
    STEP_NAMES,
)
from src.utils.logger import logger


router = Router(name="worker_tasks")


# ==== "Mening vazifalarim" ====
@router.message(IsWorker(), F.text == "📋 Mening vazifalarim")
async def show_tasks(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """Ishchining vazifalarini ko'rsatish."""
    await _send_tasks_list(message, user, session)


# ==== Yangilash ====
@router.callback_query(IsWorker(), F.data == "worker_refresh")
async def refresh_tasks(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Vazifalar ro'yxatini yangilash."""
    await callback.answer()
    await _edit_tasks_list(callback, user, session)


# ==== Bitta vazifani ko'rish ====
@router.callback_query(IsWorker(), F.data.startswith("worker_task:"))
async def view_task(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Bitta vazifani ko'rish."""
    step_id = int(callback.data.split(":")[1])

    step = await get_step_with_truck(session, step_id)
    if not step:
        await callback.answer("❌ Vazifa topilmadi", show_alert=True)
        return

    # Ishchi o'z stepidami?
    if step.step_number != user.step_number:
        await callback.answer(
            "❌ Bu sizning stepingiz emas",
            show_alert=True,
        )
        return

    await callback.answer()
    await _show_task_detail(callback.message, step)


# ==== Yordamchi funksiyalar ====
async def _send_tasks_list(
    message: Message,
    user: User,
    session: AsyncSession,
) -> None:
    """Yangi xabar bilan vazifalar ro'yxatini yuborish."""
    tasks = await get_worker_tasks(session, user.id, user.step_number)

    if not tasks:
        step_name = STEP_NAMES.get(user.step_number, f"Step {user.step_number}")
        await message.answer(
            f"📋 <b>Mening vazifalarim</b>\n\n"
            f"🔧 Bo'lim: <b>{step_name}</b>\n\n"
            f"Hozircha yangi vazifalar yo'q.\n\n"
            f"<i>Yangi ish kelganda sizga xabar beramiz.</i>",
        )
        return

    # Statistika
    new_count = sum(1 for t in tasks if t.is_pending)
    rejected_count = sum(1 for t in tasks if t.is_rejected)

    step_name = STEP_NAMES.get(user.step_number, f"Step {user.step_number}")

    text = (
        f"📋 <b>Mening vazifalarim</b>\n\n"
        f"🔧 Bo'lim: <b>{step_name}</b>\n\n"
        f"📊 Jami: <b>{len(tasks)}</b> ta\n"
    )

    if new_count > 0:
        text += f"⏳ Yangi: {new_count} ta\n"
    if rejected_count > 0:
        text += f"❌ Qaytarilgan: {rejected_count} ta\n"

    text += "\nVazifani tanlang:"

    await message.answer(
        text,
        reply_markup=worker_tasks_keyboard(tasks),
    )


async def _edit_tasks_list(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
) -> None:
    """Mavjud xabarni tahrirlab, vazifalar ro'yxatini yangilash."""
    tasks = await get_worker_tasks(session, user.id, user.step_number)

    if not tasks:
        step_name = STEP_NAMES.get(user.step_number, f"Step {user.step_number}")
        await callback.message.edit_text(
            f"📋 <b>Mening vazifalarim</b>\n\n"
            f"🔧 Bo'lim: <b>{step_name}</b>\n\n"
            f"Hozircha yangi vazifalar yo'q.",
        )
        return

    new_count = sum(1 for t in tasks if t.is_pending)
    rejected_count = sum(1 for t in tasks if t.is_rejected)

    step_name = STEP_NAMES.get(user.step_number, f"Step {user.step_number}")

    text = (
        f"📋 <b>Mening vazifalarim</b>\n\n"
        f"🔧 Bo'lim: <b>{step_name}</b>\n\n"
        f"📊 Jami: <b>{len(tasks)}</b> ta\n"
    )

    if new_count > 0:
        text += f"⏳ Yangi: {new_count} ta\n"
    if rejected_count > 0:
        text += f"❌ Qaytarilgan: {rejected_count} ta\n"

    text += "\nVazifani tanlang:"

    await callback.message.edit_text(
        text,
        reply_markup=worker_tasks_keyboard(tasks),
    )


async def _show_task_detail(message: Message, step: TruckStep) -> None:
    """Vazifa tafsilotini ko'rsatish."""
    truck = step.truck

    priority_name = PRIORITY_NAMES.get(truck.priority, truck.priority)
    step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")

    # Status
    if step.is_rejected:
        status_text = "❌ Qaytarilgan"
    else:
        status_text = "⏳ Boshlash kerak"

    text = (
        f"🚛 <b>Truck: {truck.serial_number}</b>\n\n"
    )

    if truck.model:
        text += f"🏭 Model: {truck.model}\n"
    if truck.customer:
        text += f"👤 Buyurtmachi: {truck.customer}\n"
    if truck.deadline:
        text += f"📅 Muddat: {truck.deadline.strftime('%Y-%m-%d')}\n"

    text += f"🎯 Prioritet: {priority_name}\n\n"

    text += f"🔧 Sizning stepingiz: <b>{step_name}</b>\n"
    text += f"📊 Holat: {status_text}\n"

    # Agar rejected bo'lsa — QC izohini ko'rsatamiz
    if step.is_rejected and step.qc_comment:
        text += f"\n⚠️ <b>Rad etish sababi:</b>\n"
        text += f"<i>{step.qc_comment}</i>\n"

    await message.edit_text(
        text,
        reply_markup=worker_task_detail_keyboard(step),
    )
