"""Truck bilan ishlash servisi."""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.truck import Truck
from src.database.models.truck_step import TruckStep
from src.utils.constants import TOTAL_STEPS
from src.utils.logger import logger


async def create_truck(
    session: AsyncSession,
    serial_number: str,
    model: str | None = None,
    customer: str | None = None,
    deadline: datetime | None = None,
    priority: str = "normal",
    created_by: int | None = None,
    source: str = "admin",
) -> Truck:
    """Yangi truck yaratish + 6 ta step avtomatik."""
    # Serial number unikal ekanligini tekshirish
    existing = await get_truck_by_serial(session, serial_number)
    if existing:
        raise ValueError(f"Truck '{serial_number}' allaqachon mavjud")

    truck = Truck(
        serial_number=serial_number,
        model=model,
        customer=customer,
        deadline=deadline,
        priority=priority,
        current_step=1,
        status="in_progress",
        created_by=created_by,
        source=source,
    )
    session.add(truck)
    await session.flush()

    # 6 ta step avtomatik yaratamiz
    for step_num in range(1, TOTAL_STEPS + 1):
        step = TruckStep(
            truck_id=truck.id,
            step_number=step_num,
            status="pending",
        )
        session.add(step)

    await session.flush()

    logger.success(
        f"🚛 Truck yaratildi: {serial_number} "
        f"(id={truck.id}, {TOTAL_STEPS} ta step)"
    )

    return truck


async def get_truck_by_serial(
    session: AsyncSession,
    serial_number: str,
) -> Truck | None:
    """Serial number bo'yicha truck topish."""
    stmt = select(Truck).where(Truck.serial_number == serial_number)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_truck_by_id(
    session: AsyncSession,
    truck_id: int,
) -> Truck | None:
    """ID bo'yicha truck topish."""
    return await session.get(Truck, truck_id)


async def get_trucks_page(
    session: AsyncSession,
    page: int = 0,
    per_page: int = 10,
) -> tuple[list[Truck], int]:
    """Truck ro'yxatini sahifalab olish.

    Returns:
        (trucks, total) — bu sahifadagi trucklar va jami soni
    """
    # Jami
    total_stmt = select(func.count(Truck.id))
    total_result = await session.execute(total_stmt)
    total = total_result.scalar() or 0

    # Sahifadagi trucklar
    offset = page * per_page
    stmt = (
        select(Truck)
        .order_by(
            Truck.status.asc(),  # in_progress birinchi
            Truck.priority.desc(),  # urgent birinchi
            Truck.id.desc(),  # yangilar birinchi
        )
        .offset(offset)
        .limit(per_page)
    )
    result = await session.execute(stmt)
    trucks = list(result.scalars().all())

    return trucks, total


async def delete_truck(
    session: AsyncSession,
    truck: Truck,
) -> None:
    """Truck ni o'chirish (steplari ham o'chadi — CASCADE)."""
    serial = truck.serial_number
    await session.delete(truck)
    await session.flush()

    logger.info(f"🗑 Truck o'chirildi: {serial}")
