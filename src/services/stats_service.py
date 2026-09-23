"""Statistika servisi."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.truck import Truck
from src.database.models.truck_step import TruckStep
from src.database.models.user import User
from src.utils.constants import TOTAL_STEPS


async def get_admin_stats(session: AsyncSession) -> dict:
    """Admin uchun umumiy statistika."""
    # ===== Trucklar =====
    total_trucks = (
        await session.execute(select(func.count(Truck.id)))
    ).scalar() or 0

    in_progress_trucks = (
        await session.execute(
            select(func.count(Truck.id)).where(Truck.status == "in_progress")
        )
    ).scalar() or 0

    completed_trucks = (
        await session.execute(
            select(func.count(Truck.id)).where(Truck.status == "completed")
        )
    ).scalar() or 0

    # ===== Steplar =====
    total_steps = (
        await session.execute(select(func.count(TruckStep.id)))
    ).scalar() or 0

    pending_steps = (
        await session.execute(
            select(func.count(TruckStep.id)).where(
                TruckStep.status == "pending"
            )
        )
    ).scalar() or 0

    in_review_steps = (
        await session.execute(
            select(func.count(TruckStep.id)).where(
                TruckStep.status == "in_review"
            )
        )
    ).scalar() or 0

    approved_steps = (
        await session.execute(
            select(func.count(TruckStep.id)).where(
                TruckStep.status == "approved"
            )
        )
    ).scalar() or 0

    rejected_steps = (
        await session.execute(
            select(func.count(TruckStep.id)).where(
                TruckStep.status == "rejected"
            )
        )
    ).scalar() or 0

    # ===== Foydalanuvchilar =====
    total_users = (
        await session.execute(select(func.count(User.id)))
    ).scalar() or 0

    workers_count = (
        await session.execute(
            select(func.count(User.id)).where(User.role == "worker")
        )
    ).scalar() or 0

    qc_count = (
        await session.execute(
            select(func.count(User.id)).where(User.role == "qc")
        )
    ).scalar() or 0

    admins_count = (
        await session.execute(
            select(func.count(User.id)).where(User.role == "admin")
        )
    ).scalar() or 0

    inactive_count = (
        await session.execute(
            select(func.count(User.id)).where(User.is_active == False)  # noqa: E712
        )
    ).scalar() or 0

    # ===== Har bir step bo'yicha =====
    by_step = {}
    for step_num in range(1, TOTAL_STEPS + 1):
        step_data = {}
        for status in ["pending", "in_review", "approved", "rejected"]:
            count = (
                await session.execute(
                    select(func.count(TruckStep.id))
                    .where(TruckStep.step_number == step_num)
                    .where(TruckStep.status == status)
                )
            ).scalar() or 0
            step_data[status] = count

        by_step[step_num] = step_data

    return {
        "trucks": {
            "total": total_trucks,
            "in_progress": in_progress_trucks,
            "completed": completed_trucks,
        },
        "steps": {
            "total": total_steps,
            "pending": pending_steps,
            "in_review": in_review_steps,
            "approved": approved_steps,
            "rejected": rejected_steps,
        },
        "users": {
            "total": total_users,
            "workers": workers_count,
            "qc": qc_count,
            "admins": admins_count,
            "inactive": inactive_count,
        },
        "by_step": by_step,
    }


async def get_worker_full_stats(
    session: AsyncSession,
    worker_id: int,
) -> dict:
    """Ishchi uchun to'liq statistika."""
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

    in_review = (
        await session.execute(
            select(func.count(TruckStep.id))
            .where(TruckStep.worker_id == worker_id)
            .where(TruckStep.status == "in_review")
        )
    ).scalar() or 0

    rejected = (
        await session.execute(
            select(func.count(TruckStep.id))
            .where(TruckStep.worker_id == worker_id)
            .where(TruckStep.status == "rejected")
        )
    ).scalar() or 0

    success_rate: float = 0.0
    if total > 0:
        success_rate = round((approved / total) * 100, 1)

    return {
        "total": total,
        "approved": approved,
        "in_review": in_review,
        "rejected": rejected,
        "success_rate": success_rate,
    }


async def get_qc_full_stats(
    session: AsyncSession,
    qc_id: int,
) -> dict:
    """QC uchun to'liq statistika."""
    total = (
        await session.execute(
            select(func.count(TruckStep.id)).where(TruckStep.qc_id == qc_id)
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

    approve_rate: float = 0.0
    if total > 0:
        approve_rate = round((approved / total) * 100, 1)

    return {
        "total": total,
        "approved": approved,
        "rejected": rejected,
        "approve_rate": approve_rate,
    }
