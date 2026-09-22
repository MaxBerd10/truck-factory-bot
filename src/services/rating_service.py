"""Reyting servisi (TOP ishchilar)."""
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.truck_step import TruckStep
from src.database.models.user import User


async def get_top_workers(
    session: AsyncSession,
    limit: int = 10,
) -> list[dict]:
    """TOP ishchilar reytingi (approved ishlar bo'yicha).

    Returns:
        list[dict]: [
            {
                "user_id": int,
                "full_name": str,
                "step_number": int | None,
                "total": int,      # jami ishlar
                "approved": int,   # tasdiqlangan
                "rejected": int,   # rad etilgan
                "success_rate": float,  # foiz
            },
            ...
        ]
    """
    # Har bir ishchi uchun statistika
    stmt = (
        select(
            User.id,
            User.full_name,
            User.step_number,
            func.count(TruckStep.id).label("total"),
            func.sum(
                case((TruckStep.status == "approved", 1), else_=0)
            ).label("approved"),
            func.sum(
                case((TruckStep.status == "rejected", 1), else_=0)
            ).label("rejected"),
        )
        .join(TruckStep, TruckStep.worker_id == User.id)
        .where(User.role == "worker")
        .where(User.is_active == True)  # noqa: E712
        .group_by(User.id, User.full_name, User.step_number)
        .having(func.count(TruckStep.id) > 0)
        .order_by(
            func.sum(case((TruckStep.status == "approved", 1), else_=0)).desc(),
            func.count(TruckStep.id).desc(),
        )
        .limit(limit)
    )

    result = await session.execute(stmt)

    workers = []
    for row in result:
        total = row.total or 0
        approved = row.approved or 0
        rejected = row.rejected or 0
        success_rate = round((approved / total) * 100, 1) if total > 0 else 0

        workers.append({
            "user_id": row.id,
            "full_name": row.full_name,
            "step_number": row.step_number,
            "total": total,
            "approved": approved,
            "rejected": rejected,
            "success_rate": success_rate,
        })

    return workers


async def get_worker_rank(
    session: AsyncSession,
    worker_id: int,
) -> dict:
    """Bitta ishchining reytingdagi o'rni."""
    top_workers = await get_top_workers(session, limit=1000)

    for idx, worker in enumerate(top_workers, start=1):
        if worker["user_id"] == worker_id:
            return {
                "rank": idx,
                "total_workers": len(top_workers),
                **worker,
            }

    return {
        "rank": None,
        "total_workers": len(top_workers),
        "user_id": worker_id,
        "full_name": "—",
        "step_number": None,
        "total": 0,
        "approved": 0,
        "rejected": 0,
        "success_rate": 0,
    }
