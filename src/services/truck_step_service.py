"""TruckStep bilan ishlash servisi."""
from datetime import datetime, timezone

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.truck import Truck
from src.database.models.truck_step import TruckStep
from src.services.notification_service import notify_qc_new_work
from src.utils.logger import logger


async def get_worker_tasks(
    session: AsyncSession,
    worker_id: int,
    step_number: int,
) -> list[TruckStep]:
    """Ishchining vazifalarini olish.

    Faqat:
    - Shu ishchining stepidagi
    - `pending` yoki `rejected` holatidagi
    - Truck `in_progress` bo'lgan
    - **Truck.current_step == step_number** (joriy step)
    """
    stmt = (
        select(TruckStep)
        .join(Truck, TruckStep.truck_id == Truck.id)
        .where(TruckStep.step_number == step_number)
        .where(TruckStep.status.in_(["pending", "rejected"]))
        .where(Truck.status == "in_progress")
        .where(Truck.current_step == step_number)
        .options(selectinload(TruckStep.truck))
        .order_by(
            Truck.priority.desc(),
            Truck.deadline.asc().nulls_last(),
            Truck.id.desc(),
        )
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_step_by_id(
    session: AsyncSession,
    step_id: int,
) -> TruckStep | None:
    """ID bo'yicha step topish."""
    return await session.get(TruckStep, step_id)


async def get_step_with_truck(
    session: AsyncSession,
    step_id: int,
) -> TruckStep | None:
    """ID bo'yicha step topish (truck va worker bilan)."""
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


async def claim_step(
    session: AsyncSession,
    step: TruckStep,
    worker_id: int,
) -> TruckStep:
    """Stepni ishchiga biriktirish (boshlash)."""
    step.worker_id = worker_id
    step.started_at = datetime.now(timezone.utc)
    await session.flush()

    logger.info(
        f"🔧 Step boshlandi: truck_id={step.truck_id}, "
        f"step={step.step_number}, worker_id={worker_id}"
    )

    return step


async def submit_step(
    session: AsyncSession,
    step: TruckStep,
    worker_id: int,
    media_type: str,
    media_file_id: str,
    media_local_path: str | None = None,
    worker_comment: str | None = None,
    bot: Bot | None = None,
) -> TruckStep:
    """Ishchi stepni yuboradi (QC tekshiruviga).

    Args:
        bot: Agar berilsa — QC ga bildirishnoma yuboriladi
    """
    step.worker_id = worker_id
    step.status = "in_review"
    step.media_type = media_type
    step.media_file_id = media_file_id
    step.media_local_path = media_local_path
    step.worker_comment = worker_comment
    step.submitted_at = datetime.now(timezone.utc)

    # Agar ilgari rejected bo'lsa — qc_comment ni tozalash
    step.qc_comment = None
    step.qc_id = None
    step.reviewed_at = None

    await session.flush()

    logger.success(
        f"📤 Step yuborildi: truck_id={step.truck_id}, "
        f"step={step.step_number}, worker_id={worker_id}, "
        f"media={media_type}"
    )

    # QC ga bildirishnoma
    if bot:
        try:
            await notify_qc_new_work(bot, session, step)
        except Exception as e:
            logger.error(f"❌ QC bildirishnoma xatosi: {e}")

    return step


async def get_worker_history(
    session: AsyncSession,
    worker_id: int,
    limit: int = 30,
) -> list[TruckStep]:
    """Ishchining tarixini olish (yuborilgan ishlar)."""
    stmt = (
        select(TruckStep)
        .where(TruckStep.worker_id == worker_id)
        .where(TruckStep.status.in_(["in_review", "approved", "rejected"]))
        .options(selectinload(TruckStep.truck))
        .order_by(TruckStep.submitted_at.desc().nulls_last())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_worker_stats(
    session: AsyncSession,
    worker_id: int,
) -> dict[str, int]:
    """Ishchining statistikasi."""
    from sqlalchemy import func

    total_stmt = (
        select(func.count(TruckStep.id))
        .where(TruckStep.worker_id == worker_id)
    )
    total = (await session.execute(total_stmt)).scalar() or 0

    approved_stmt = (
        select(func.count(TruckStep.id))
        .where(TruckStep.worker_id == worker_id)
        .where(TruckStep.status == "approved")
    )
    approved = (await session.execute(approved_stmt)).scalar() or 0

    in_review_stmt = (
        select(func.count(TruckStep.id))
        .where(TruckStep.worker_id == worker_id)
        .where(TruckStep.status == "in_review")
    )
    in_review = (await session.execute(in_review_stmt)).scalar() or 0

    rejected_stmt = (
        select(func.count(TruckStep.id))
        .where(TruckStep.worker_id == worker_id)
        .where(TruckStep.status == "rejected")
    )
    rejected = (await session.execute(rejected_stmt)).scalar() or 0

    return {
        "total": total,
        "approved": approved,
        "in_review": in_review,
        "rejected": rejected,
    }
