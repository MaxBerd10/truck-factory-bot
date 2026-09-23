"""Servislar uchun unit testlar."""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.truck import Truck
from src.database.models.truck_step import TruckStep
from src.database.models.user import User
from src.services.stats_service import (
    get_admin_stats,
    get_qc_full_stats,
    get_worker_full_stats,
)
from src.services.truck_step_service import (
    get_step_with_truck,
    get_worker_tasks,
)


# ==================== TESTLAR ====================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_worker_full_stats_empty(session: AsyncSession):
    """Yangi ishchining statistikasi — bo'sh."""
    user = User(
        telegram_id=111111111,
        full_name="Yangi Ishchi",
        role="worker",
        step_number=1,
        is_active=True,
    )
    session.add(user)
    await session.flush()

    stats = await get_worker_full_stats(session, user.id)

    assert stats["total"] == 0
    assert stats["approved"] == 0
    assert stats["rejected"] == 0
    assert stats["in_review"] == 0
    assert stats["success_rate"] == 0.0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_qc_full_stats_empty(session: AsyncSession):
    """Yangi QC statistikasi — bo'sh."""
    qc = User(
        telegram_id=222222222,
        full_name="Yangi QC",
        role="qc",
        is_active=True,
    )
    session.add(qc)
    await session.flush()

    stats = await get_qc_full_stats(session, qc.id)

    assert stats["total"] == 0
    assert stats["approved"] == 0
    assert stats["rejected"] == 0
    assert stats["approve_rate"] == 0.0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_admin_stats_empty(session: AsyncSession):
    """Admin statistikasi — bo'sh."""
    stats = await get_admin_stats(session)

    assert "trucks" in stats
    assert "steps" in stats
    assert "users" in stats
    assert "by_step" in stats
    assert stats["trucks"]["total"] >= 0
    assert stats["steps"]["total"] >= 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_worker_tasks_empty(session: AsyncSession):
    """Ishchining vazifalari — bo'sh (truck yo'q)."""
    user = User(
        telegram_id=333333333,
        full_name="Test Ishchi",
        role="worker",
        step_number=1,
        is_active=True,
    )
    session.add(user)
    await session.flush()

    tasks = await get_worker_tasks(session, user.id, 1)
    assert len(tasks) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_worker_tasks_with_truck(session: AsyncSession):
    """Ishchining vazifalari — 1 ta (truck bor)."""
    # Ishchi
    user = User(
        telegram_id=444444444,
        full_name="Test Ishchi 2",
        role="worker",
        step_number=1,
        is_active=True,
    )
    session.add(user)
    await session.flush()

    # Truck
    truck = Truck(
        serial_number="TR-TEST-001",
        model="Test Model",
        customer="Test Customer",
        priority="normal",
        current_step=1,
        status="in_progress",
        source="admin",
    )
    session.add(truck)
    await session.flush()

    # Step
    step = TruckStep(
        truck_id=truck.id,
        step_number=1,
        status="pending",
    )
    session.add(step)
    await session.flush()

    # Test
    tasks = await get_worker_tasks(session, user.id, 1)

    assert len(tasks) == 1
    assert tasks[0].truck_id == truck.id
    assert tasks[0].step_number == 1
    assert tasks[0].status == "pending"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_step_with_truck(session: AsyncSession):
    """Stepni truck bilan olish."""
    # Truck
    truck = Truck(
        serial_number="TR-TEST-002",
        model="Test Model 2",
        customer="Test Customer 2",
        priority="normal",
        current_step=1,
        status="in_progress",
        source="admin",
    )
    session.add(truck)
    await session.flush()

    # Step
    step = TruckStep(
        truck_id=truck.id,
        step_number=1,
        status="pending",
    )
    session.add(step)
    await session.flush()

    # Test
    loaded_step = await get_step_with_truck(session, step.id)

    assert loaded_step is not None
    assert loaded_step.truck.serial_number == "TR-TEST-002"
    assert loaded_step.step_number == 1
