"""QC (Sifat nazoratchisi) servisi."""
from datetime import datetime, timezone

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.truck import Truck
from src.database.models.truck_step import TruckStep
from src.services.notification_service import (
    notify_admin_truck_completed,
    notify_next_worker,
    notify_worker_approved,
    notify_worker_rejected,
)
from src.utils.constants import TOTAL_STEPS
from src.utils.logger import logger


async def get_qc_queue(
    session: AsyncSession,
    limit: int = 50,
) -> list[TruckStep]:
    """Tekshirish navbatini olish."""
    stmt = (
        select(TruckStep)
        .join(Truck, TruckStep.truck_id == Truck.id)
        .where(TruckStep.status == "in_review")
        .where(Truck.status == "in_progress")
        .options(
            selectinload(TruckStep.truck),
            selectinload(TruckStep.worker),
        )
        .order_by(
            Truck.priority.desc(),
            TruckStep.submitted_at.asc(),
        )
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_step_for_review(
    session: AsyncSession,
    step_id: int,
) -> TruckStep | None:
    """Stepni ko'rish uchun olish (truck va worker bilan)."""
    stmt = (
        select(TruckStep)
        .where(TruckStep.id == step_id)
        .options(
            selectinload(TruckStep.truck),
            selectinload(TruckStep.worker),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def approve_step(
    session: AsyncSession,
    step: TruckStep,
    qc_id: int,
    bot: Bot | None = None,
) -> Truck:
    """Stepni tasdiqlash.

    Args:
        bot: Agar berilsa — ishchi, keyingi ishchi va adminga bildirishnoma

    Returns:
        Yangilangan Truck
    """
    step.status = "approved"
    step.qc_id = qc_id
    step.reviewed_at = datetime.now(timezone.utc)

    truck = step.truck

    # Keyingi stepga o'tamiz
    if step.step_number < TOTAL_STEPS:
        truck.current_step = step.step_number + 1

        logger.success(
            f"✅ Step tasdiqlandi: truck_id={truck.id}, "
            f"step={step.step_number} → keyingi step: {truck.current_step}, "
            f"qc_id={qc_id}"
        )
    else:
        # Oxirgi step — truck tayyor
        truck.status = "completed"
        truck.completed_at = datetime.now(timezone.utc)

        logger.success(
            f"🎉 Truck TAYYOR: {truck.serial_number} "
            f"(barcha {TOTAL_STEPS} step tasdiqlandi), "
            f"qc_id={qc_id}"
        )

    await session.flush()

    # ===== Bildirishnomalar =====
    if bot:
        try:
            # 1. Ishchiga "tasdiqlandi"
            await notify_worker_approved(bot, session, step)

            # 2. Truck tayyor bo'lsa — adminga
            if truck.is_completed:
                await notify_admin_truck_completed(bot, session, truck)
            else:
                # 3. Keyingi step ishchisiga "yangi vazifa"
                await notify_next_worker(
                    bot, session, truck, truck.current_step
                )
        except Exception as e:
            logger.error(f"❌ Bildirishnoma xatosi (approve): {e}")

    return truck


async def reject_step(
    session: AsyncSession,
    step: TruckStep,
    qc_id: int,
    reason: str,
    bot: Bot | None = None,
) -> TruckStep:
    """Stepni rad etish.

    Args:
        bot: Agar berilsa — ishchiga bildirishnoma
    """
    step.status = "rejected"
    step.qc_id = qc_id
    step.qc_comment = reason
    step.reviewed_at = datetime.now(timezone.utc)

    logger.warning(
        f"❌ Step rad etildi: truck_id={step.truck_id}, "
        f"step={step.step_number}, qc_id={qc_id}, "
        f"sabab='{reason}'"
    )

    await session.flush()

    # ===== Bildirishnoma =====
    if bot:
        try:
            await notify_worker_rejected(bot, session, step)
        except Exception as e:
            logger.error(f"❌ Bildirishnoma xatosi (reject): {e}")

    return step


async def get_qc_history(
    session: AsyncSession,
    qc_id: int,
    limit: int = 30,
) -> list[TruckStep]:
    """QC tekshirgan ishlar tarixi."""
    stmt = (
        select(TruckStep)
        .where(TruckStep.qc_id == qc_id)
        .where(TruckStep.status.in_(["approved", "rejected"]))
        .options(
            selectinload(TruckStep.truck),
            selectinload(TruckStep.worker),
        )
        .order_by(TruckStep.reviewed_at.desc().nulls_last())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_qc_stats(
    session: AsyncSession,
    qc_id: int,
) -> dict[str, int]:
    """QC statistikasi."""
    from sqlalchemy import func

    total_stmt = (
        select(func.count(TruckStep.id))
        .where(TruckStep.qc_id == qc_id)
    )
    total = (await session.execute(total_stmt)).scalar() or 0

    approved_stmt = (
        select(func.count(TruckStep.id))
        .where(TruckStep.qc_id == qc_id)
        .where(TruckStep.status == "approved")
    )
    approved = (await session.execute(approved_stmt)).scalar() or 0

    rejected_stmt = (
        select(func.count(TruckStep.id))
        .where(TruckStep.qc_id == qc_id)
        .where(TruckStep.status == "rejected")
    )
    rejected = (await session.execute(rejected_stmt)).scalar() or 0

    return {
        "total": total,
        "approved": approved,
        "rejected": rejected,
    }


async def get_queue_count(session: AsyncSession) -> int:
    """Navbatdagi ishlar soni."""
    from sqlalchemy import func

    stmt = (
        select(func.count(TruckStep.id))
        .where(TruckStep.status == "in_review")
    )
    result = await session.execute(stmt)
    return result.scalar() or 0
