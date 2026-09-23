"""Bildirishnoma servisi."""
from aiogram import Bot

from src.database.models.truck import Truck
from src.database.models.truck_step import TruckStep
from src.database.models.user import User
from src.utils.constants import (
    PRIORITY_NAMES,
    STEP_NAMES,
)
from src.utils.logger import logger


async def notify_qc_new_work(
    bot: Bot,
    step: TruckStep,
    qc_telegram_ids: list[int],
) -> None:
    """QC ga yangi ish haqida xabar."""
    truck = step.truck
    worker = step.worker

    priority_name = PRIORITY_NAMES.get(truck.priority, truck.priority)
    step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")

    text = (
        f"🔔 <b>Yangi ish keldi!</b>\n\n"
        f"🚛 Truck: <b>{truck.serial_number}</b>\n"
        f"🔧 Step: <b>{step_name}</b>\n"
        f"🎯 Prioritet: {priority_name}\n"
    )

    if worker:
        text += f"👷 Ishchi: {worker.full_name}\n"

    if step.worker_comment:
        text += f"\n📝 Izoh: <i>{step.worker_comment}</i>\n"

    text += "\n🔔 Navbatni ko'rish uchun \"🔔 Tekshirish navbati\" ni bosing."

    for tg_id in qc_telegram_ids:
        try:
            await bot.send_message(tg_id, text)
        except Exception as e:
            logger.warning(f"⚠️ QC {tg_id} ga yuborilmadi: {e}")


async def notify_worker_approved(
    bot: Bot,
    step: TruckStep,
    next_step_number: int | None = None,
) -> None:
    """Ishchiga ishi tasdiqlangani haqida xabar."""
    if not step.worker:
        return

    truck = step.truck
    step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")

    text = (
        f"✅ <b>Isingiz tasdiqlandi!</b>\n\n"
        f"🚛 Truck: <b>{truck.serial_number}</b>\n"
        f"🔧 Step: <b>{step_name}</b>\n"
    )

    if next_step_number and next_step_number <= 6:
        next_step_name = STEP_NAMES.get(
            next_step_number, f"Step {next_step_number}"
        )
        text += f"\n📍 Keyingi step: <b>{next_step_name}</b>\n"

    try:
        await bot.send_message(step.worker.telegram_id, text)
    except Exception as e:
        logger.warning(f"⚠️ Ishchi {step.worker.id} ga yuborilmadi: {e}")


async def notify_worker_rejected(
    bot: Bot,
    step: TruckStep,
    reason: str,
) -> None:
    """Ishchiga ishi rad etilgani haqida xabar."""
    if not step.worker:
        return

    truck = step.truck
    step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")

    text = (
        f"❌ <b>Isingiz rad etildi</b>\n\n"
        f"🚛 Truck: <b>{truck.serial_number}</b>\n"
        f"🔧 Step: <b>{step_name}</b>\n\n"
        f"📝 <b>Sabab:</b>\n<i>{reason}</i>\n\n"
        f"🔄 Qayta yuborish uchun \"📋 Mening vazifalarim\" ni bosing."
    )

    try:
        await bot.send_message(step.worker.telegram_id, text)
    except Exception as e:
        logger.warning(f"⚠️ Ishchi {step.worker.id} ga yuborilmadi: {e}")


async def notify_next_worker(
    bot: Bot,
    truck: Truck,
    step_number: int,
    workers: list[User],
) -> None:
    """Keyingi step ishchisiga xabar."""
    if not workers:
        logger.warning(
            f"⚠️ Step {step_number} uchun ishchi topilmadi — "
            f"bildirishnoma yuborilmadi"
        )
        return

    step_name = STEP_NAMES.get(step_number, f"Step {step_number}")
    priority_name = PRIORITY_NAMES.get(truck.priority, truck.priority)

    text = (
        f"🔔 <b>Yangi vazifa!</b>\n\n"
        f"🚛 Truck: <b>{truck.serial_number}</b>\n"
        f"🔧 Step: <b>{step_name}</b>\n"
        f"🎯 Prioritet: {priority_name}\n"
    )

    if truck.deadline:
        text += f"📅 Muddat: {truck.deadline.strftime('%Y-%m-%d')}\n"

    text += "\n📋 \"Mening vazifalarim\" ni bosing."

    for worker in workers:
        if not worker.telegram_id:
            continue
        try:
            await bot.send_message(worker.telegram_id, text)
        except Exception as e:
            logger.warning(f"⚠️ Ishchi {worker.id} ga yuborilmadi: {e}")


async def notify_admin_truck_completed(
    bot: Bot,
    truck: Truck,
    admin_telegram_ids: list[int],
) -> None:
    """Adminlarga truck tayyor bo'lgani haqida xabar."""
    text = (
        f"🎉 <b>TRUCK TAYYOR!</b>\n\n"
        f"🚛 <b>{truck.serial_number}</b>\n"
    )

    if truck.model:
        text += f"🏭 {truck.model}\n"
    if truck.customer:
        text += f"👤 {truck.customer}\n"
    if truck.deadline:
        text += f"📅 Muddat: {truck.deadline.strftime('%Y-%m-%d')}\n"

    text += "\n✅ Barcha 6 ta step tasdiqlandi!"

    for tg_id in admin_telegram_ids:
        if not tg_id:
            continue
        try:
            await bot.send_message(tg_id, text)
        except Exception as e:
            logger.warning(f"⚠️ Admin {tg_id} ga yuborilmadi: {e}")
