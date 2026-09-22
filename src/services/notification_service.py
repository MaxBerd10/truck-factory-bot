"""Bildirishnoma yuborish servisi."""
from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
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
    session: AsyncSession,
    step: TruckStep,
) -> None:
    """QC ga yangi ish haqida xabar."""
    truck = step.truck
    worker = step.worker

    # Barcha QC larni olamiz
    stmt = (
        select(User)
        .where(User.role == "qc")
        .where(User.is_active == True)  # noqa: E712
    )
    result = await session.execute(stmt)
    qc_users = list(result.scalars().all())

    if not qc_users:
        logger.warning("⚠️ Hech qanday QC topilmadi — bildirishnoma yuborilmadi")
        return

    step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")
    priority_name = PRIORITY_NAMES.get(truck.priority, truck.priority)

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

    text += f"\n🔔 Navbatni ko'rish uchun \"🔔 Tekshirish navbati\" ni bosing."

    # Har bir QC ga yuboramiz
    for qc in qc_users:
        try:
            await bot.send_message(qc.telegram_id, text)
            logger.info(f"📨 QC ga xabar yuborildi: {qc.full_name}")
        except Exception as e:
            logger.error(f"❌ QC ga xabar yuborishda xato ({qc.id}): {e}")


async def notify_worker_approved(
    bot: Bot,
    session: AsyncSession,
    step: TruckStep,
) -> None:
    """Ishchiga "tasdiqlandi" xabari."""
    worker = step.worker
    if not worker:
        return

    truck = step.truck
    step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")

    text = (
        f"✅ <b>Isingiz tasdiqlandi!</b>\n\n"
        f"🚛 Truck: <b>{truck.serial_number}</b>\n"
        f"🔧 Step: <b>{step_name}</b>\n\n"
    )

    if truck.is_completed:
        text += "🎉 <b>Truck TAYYOR bo'ldi!</b>\n"
    else:
        next_step_name = STEP_NAMES.get(
            truck.current_step, f"Step {truck.current_step}"
        )
        text += f"📍 Keyingi step: <b>{next_step_name}</b>\n"

    try:
        await bot.send_message(worker.telegram_id, text)
        logger.info(f"📨 Ishchiga xabar yuborildi: {worker.full_name}")
    except Exception as e:
        logger.error(f"❌ Ishchiga xabar yuborishda xato ({worker.id}): {e}")


async def notify_worker_rejected(
    bot: Bot,
    session: AsyncSession,
    step: TruckStep,
) -> None:
    """Ishchiga "rad etildi" xabari."""
    worker = step.worker
    if not worker:
        return

    truck = step.truck
    step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")

    text = (
        f"❌ <b>Isingiz rad etildi</b>\n\n"
        f"🚛 Truck: <b>{truck.serial_number}</b>\n"
        f"🔧 Step: <b>{step_name}</b>\n\n"
    )

    if step.qc_comment:
        text += f"📝 <b>Sabab:</b>\n<i>{step.qc_comment}</i>\n\n"

    text += (
        f"🔄 Qayta yuborish uchun \"📋 Mening vazifalarim\" ni bosing."
    )

    try:
        await bot.send_message(worker.telegram_id, text)
        logger.info(f"📨 Ishchiga (rad) xabar yuborildi: {worker.full_name}")
    except Exception as e:
        logger.error(f"❌ Ishchiga xabar yuborishda xato ({worker.id}): {e}")


async def notify_next_worker(
    bot: Bot,
    session: AsyncSession,
    truck: Truck,
    step_number: int,
) -> None:
    """Keyingi step ishchisiga xabar."""
    # Bu step uchun ishchi(lar)ni topamiz
    stmt = (
        select(User)
        .where(User.role == "worker")
        .where(User.step_number == step_number)
        .where(User.is_active == True)  # noqa: E712
    )
    result = await session.execute(stmt)
    workers = list(result.scalars().all())

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

    text += f"\n📋 \"Mening vazifalarim\" ni bosing."

    for worker in workers:
        try:
            await bot.send_message(worker.telegram_id, text)
            logger.info(
                f"📨 Keyingi ishchiga xabar: {worker.full_name} "
                f"(step {step_number})"
            )
        except Exception as e:
            logger.error(
                f"❌ Keyingi ishchiga xabar yuborishda xato "
                f"({worker.id}): {e}"
            )


async def notify_admin_truck_completed(
    bot: Bot,
    session: AsyncSession,
    truck: Truck,
) -> None:
    """Adminlarga "truck tayyor" xabari."""
    # Barcha adminlarni olamiz (DB dan)
    stmt = (
        select(User)
        .where(User.role == "admin")
        .where(User.is_active == True)  # noqa: E712
    )
    result = await session.execute(stmt)
    admins = list(result.scalars().all())

    # ADMIN_IDS dan ham qo'shamiz (agar DB da bo'lmasa)
    admin_telegram_ids = {a.telegram_id for a in admins}
    for admin_id in settings.ADMIN_IDS:
        if admin_id not in admin_telegram_ids:
            admins.append(None)  # placeholder
            admin_telegram_ids.add(admin_id)

    if not admins:
        logger.warning("⚠️ Hech qanday admin topilmadi")
        return

    text = (
        f"🎉 <b>TRUCK TAYYOR!</b>\n\n"
        f"🚛 <b>{truck.serial_number}</b>\n"
    )

    if truck.model:
        text += f"🏭 Model: {truck.model}\n"
    if truck.customer:
        text += f"👤 Buyurtmachi: {truck.customer}\n"
    if truck.deadline:
        text += f"📅 Muddat: {truck.deadline.strftime('%Y-%m-%d')}\n"

    text += f"\n✅ Barcha 6 ta step tasdiqlandi!"

    for admin in admins:
        if admin is None:
            continue
        try:
            await bot.send_message(admin.telegram_id, text)
            logger.info(f"📨 Adminga xabar: {admin.full_name}")
        except Exception as e:
            logger.error(f"❌ Adminga xabar yuborishda xato ({admin.id}): {e}")

    # ADMIN_IDS dan qolganlar
    for admin_id in settings.ADMIN_IDS:
        if admin_id in {a.telegram_id for a in admins if a}:
            continue
        try:
            await bot.send_message(admin_id, text)
            logger.info(f"📨 Adminga xabar (env): {admin_id}")
        except Exception as e:
            logger.error(f"❌ Adminga xabar yuborishda xato ({admin_id}): {e}")
