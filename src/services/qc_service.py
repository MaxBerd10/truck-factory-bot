"""QC (Sifat nazoratchisi) servisi."""
from datetime import UTC, datetime

from aiogram import Bot
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.truck import Truck
from src.database.models.truck_step import TruckStep
from src.database.models.user import User
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
    limit: int = 20,
) -> list[TruckStep]:
    """QC navbatini olish (in_review steplar)."""
    stmt = (
        select(TruckStep)
        .where(TruckStep.status == "in_review")
        .options(
            selectinload(TruckStep.truck),
            selectinload(TruckStep.worker),
        )
        .order_by(
            Truck.priority.desc(),
            Truck.deadline.asc().nulls_last(),
            TruckStep.submitted_at.asc().nulls_last(),
        )
        .join(Truck, TruckStep.truck_id == Truck.id)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_queue_count(session: AsyncSession) -> int:
    """Navbatdagi ishlar soni."""
    result = await session.execute(
        select(func.count(TruckStep.id)).where(
            TruckStep.status == "in_review"
        )
    )
    return result.scalar() or 0


async def get_step_for_review(
    session: AsyncSession,
    step_id: int,
) -> TruckStep | None:
    """Tekshirish uchun stepni olish."""
    stmt = (
        select(TruckStep)
        .where(TruckStep.id == step_id)
        .options(
            selectinload(TruckStep.truck),
            selectinload(TruckStep.worker),
            selectinload(TruckStep.qc),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def approve_step(
    session: AsyncSession,
    step: TruckStep,
    qc_id: int,
    bot: Bot,
) -> Truck:
    """Stepni tasdiqlash."""
    # Step ni yangilash
    step.status = "approved"
    step.qc_id = qc_id
    step.reviewed_at = datetime.now(UTC)

    truck = step.truck

    # Keyingi stepga o'tish
    if step.step_number < TOTAL_STEPS:
        truck.current_step = step.step_number + 1
    else:
        # Oxirgi step — truck tayyor
        truck.status = "completed"
        truck.completed_at = datetime.now(UTC)

    await session.flush()

    logger.success(
        f"✅ Step tasdiqlandi: truck_id={truck.id}, "
        f"step={step.step_number}, qc_id={qc_id}"
    )

    # ==== Bildirishnomalar ====
    try:
        # 1. Ishchiga xabar
        await notify_worker_approved(
            bot, step, next_step_number=truck.current_step
        )

        # 2. Agar truck tugagan bo'lsa — adminlarga
        if truck.is_completed:
            admin_stmt = select(User.telegram_id).where(
                User.role == "admin",
                User.is_active == True,  # noqa: E712
            )
            admin_result = await session.execute(admin_stmt)
            admin_tg_ids = [row[0] for row in admin_result if row[0]]

            if admin_tg_ids:
                await notify_admin_truck_completed(
                    bot, truck, admin_tg_ids
                )
                logger.info(
                    f"📨 Adminga xabar yuborildi: "
                    f"{len(admin_tg_ids)} ta admin"
                )
        else:
            # 3. Keyingi step ishchisiga xabar
            workers_stmt = select(User).where(
                User.role == "worker",
                User.step_number == truck.current_step,
                User.is_active == True,  # noqa: E712
            )
            workers_result = await session.execute(workers_stmt)
            workers = list(workers_result.scalars().all())

            await notify_next_worker(
                bot, truck, truck.current_step, workers
            )

    except Exception as e:
        logger.error(f"❌ Bildirishnoma yuborishda xato: {e}")

    return truck


async def reject_step(
    session: AsyncSession,
    step: TruckStep,
    qc_id: int,
    reason: str,
    bot: Bot,
) -> None:
    """Stepni rad etish."""
    step.status = "rejected"
    step.qc_id = qc_id
    step.qc_comment = reason
    step.reviewed_at = datetime.now(UTC)

    await session.flush()

    logger.warning(
        f"❌ Step rad etildi: truck_id={step.truck_id}, "
        f"step={step.step_number}, qc_id={qc_id}, sabab={reason}"
    )

    # ==== Ishchiga xabar ====
    try:
        await notify_worker_rejected(bot, step, reason)
        logger.info("📨 Ishchiga rad etish xabari yuborildi")
    except Exception as e:
        logger.error(f"❌ Ishchiga xabar yuborishda xato: {e}")


async def get_qc_history(
    session: AsyncSession,
    qc_id: int,
    limit: int = 10,
) -> list[TruckStep]:
    """QC ning oxirgi tekshirishlari."""
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
) -> dict:
    """QC statistikasi."""
    total = (
        await session.execute(
            select(func.count(TruckStep.id)).where(
                TruckStep.qc_id == qc_id
            )
        )
    ).scalar() or 0

    approved = (
        await session.execute(
            select(func.count(TruckStep.id))
            .where(TruckStep.qc_id == qc_id)
            .where(TruckStep.status == "approved")
        )
    ).scalar() or 0

    rejected = (
        await session.execute(
            select(func.count(TruckStep.id))
            .where(TruckStep.qc_id == qc_id)
            .where(TruckStep.status == "rejected")
        )
    ).scalar() or 0

    return {
        "total": total,
        "approved": approved,
        "rejected": rejected,
    }
