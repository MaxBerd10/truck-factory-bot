"""QC (Sifat nazoratchisi) servisi."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.truck import Truck
from src.database.models.truck_step import TruckStep
from src.utils.constants import TOTAL_STEPS
from src.utils.logger import logger


async def get_qc_queue(
    session: AsyncSession,
    limit: int = 50,
) -> list[TruckStep]:
    """Tekshirish navbatini olish.

    Faqat `in_review` holatidagi steplar.
    Eng eski (avval yuborilgan) birinchi.
    """
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
            Truck.priority.desc(),  # urgent birinchi
            TruckStep.submitted_at.asc(),  # eski birinchi
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
) -> Truck:
    """Stepni tasdiqlash.

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
    return truck


async def reject_step(
    session: AsyncSession,
    step: TruckStep,
    qc_id: int,
    reason: str,
) -> TruckStep:
    """Stepni rad etish."""
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

    # Jami
    total_stmt = (
        select(func.count(TruckStep.id))
        .where(TruckStep.qc_id == qc_id)
    )
    total = (await session.execute(total_stmt)).scalar() or 0

    # Approved
    approved_stmt = (
        select(func.count(TruckStep.id))
        .where(TruckStep.qc_id == qc_id)
        .where(TruckStep.status == "approved")
    )
    approved = (await session.execute(approved_stmt)).scalar() or 0

    # Rejected
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
