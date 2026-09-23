"""TruckStep bilan ishlash servisi."""
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.truck import Truck
from src.database.models.truck_step import TruckStep
from src.database.models.user import User
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
    """Stepni ID bo'yicha olish."""
    return await session.get(TruckStep, step_id)


async def get_step_with_truck(
    session: AsyncSession,
    step_id: int,
) -> TruckStep | None:
    """Stepni truck bilan birga olish."""
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


async def claim_step(
    session: AsyncSession,
    step: TruckStep,
    worker_id: int,
) -> None:
    """Stepni ishchiga biriktirish (boshlash)."""
    step.worker_id = worker_id
    step.started_at = datetime.now(UTC)
    await session.flush()


async def submit_step(
    session: AsyncSession,
    step: TruckStep,
    worker_id: int,
    media_type: str,
    media_file_id: str,
    media_local_path: str | None,
    worker_comment: str | None,
    bot,
) -> None:
    """Ishni yuborish (QC ga)."""
    # Step ni yangilash
    step.worker_id = worker_id
    step.status = "in_review"
    step.media_type = media_type
    step.media_file_id = media_file_id
    step.media_local_path = media_local_path
    step.worker_comment = worker_comment
    step.submitted_at = datetime.now(UTC)

    # Agar ilgari rejected bo'lsa — qc_comment ni tozalash
    if step.status == "rejected":
        step.qc_comment = None
        step.qc_id = None
        step.reviewed_at = None

    await session.flush()

    logger.info(
        f"📤 Step yuborildi: truck_id={step.truck_id}, "
        f"step={step.step_number}, worker_id={worker_id}, "
        f"media={media_type}"
    )

    # ==== QC ga bildirishnoma ====
    try:
        # Faol QC larni olish
        qc_stmt = select(User).where(
            User.role == "qc",
            User.is_active == True,  # noqa: E712
        )
        qc_result = await session.execute(qc_stmt)
        qcs = list(qc_result.scalars().all())

        qc_telegram_ids = [
            qc.telegram_id for qc in qcs if qc.telegram_id
        ]

        if qc_telegram_ids:
            await notify_qc_new_work(bot, step, qc_telegram_ids)
            logger.info(
                f"📨 QC ga xabar yuborildi: "
                f"{len(qc_telegram_ids)} ta QC"
            )
        else:
            logger.warning("⚠️ Faol QC topilmadi — bildirishnoma yuborilmadi")

    except Exception as e:
        logger.error(f"❌ QC ga bildirishnoma yuborishda xato: {e}")


async def get_worker_history(
    session: AsyncSession,
    worker_id: int,
    limit: int = 10,
) -> list[TruckStep]:
    """Ishchining oxirgi ishlari."""
    stmt = (
        select(TruckStep)
        .where(TruckStep.worker_id == worker_id)
        .where(TruckStep.status.in_(["approved", "rejected", "in_review"]))
        .options(selectinload(TruckStep.truck))
        .order_by(TruckStep.submitted_at.desc().nulls_last())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_worker_stats(
    session: AsyncSession,
    worker_id: int,
) -> dict:
    """Ishchining statistikasi."""
    from sqlalchemy import func

    total = (
        await session.execute(
            select(func.count(TruckStep.id)).where(
                TruckStep.worker_id == worker_id
            )
        )
    ).scalar() or 0

    approved = (
        await session.execute(
            select(func.count(TruckStep.id))
            .where(TruckStep.worker_id == worker_id)
            .where(TruckStep.status == "approved")
        )
    ).scalar() or 0

    rejected = (
        await session.execute(
            select(func.count(TruckStep.id))
            .where(TruckStep.worker_id == worker_id)
            .where(TruckStep.status == "rejected")
        )
    ).scalar() or 0

    in_review = (
        await session.execute(
            select(func.count(TruckStep.id))
            .where(TruckStep.worker_id == worker_id)
            .where(TruckStep.status == "in_review")
        )
    ).scalar() or 0

    return {
        "total": total,
        "approved": approved,
        "rejected": rejected,
        "in_review": in_review,
    }
