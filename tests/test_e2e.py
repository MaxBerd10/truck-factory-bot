"""E2E testlar (to'liq oqim)."""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.truck import Truck
from src.database.models.truck_step import TruckStep
from src.database.models.user import User
from src.services.qc_service import approve_step, reject_step
from src.services.truck_step_service import (
    claim_step,
    get_step_with_truck,
    get_worker_tasks,
)
from src.utils.constants import TOTAL_STEPS


# ==================== YORDAMCHI FUNKSIYALAR ====================

async def create_worker(
    session: AsyncSession,
    step_number: int,
    telegram_id: int,
) -> User:
    """Ishchi yaratish."""
    user = User(
        telegram_id=telegram_id,
        full_name=f"Ishchi Step {step_number}",
        role="worker",
        step_number=step_number,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user


async def create_qc(
    session: AsyncSession,
    telegram_id: int,
) -> User:
    """QC yaratish."""
    qc = User(
        telegram_id=telegram_id,
        full_name="Test QC",
        role="qc",
        is_active=True,
    )
    session.add(qc)
    await session.flush()
    return qc


async def create_admin(
    session: AsyncSession,
    telegram_id: int,
) -> User:
    """Admin yaratish."""
    admin = User(
        telegram_id=telegram_id,
        full_name="Test Admin",
        role="admin",
        is_active=True,
    )
    session.add(admin)
    await session.flush()
    return admin


async def create_truck_with_steps(
    session: AsyncSession,
    serial_number: str,
) -> Truck:
    """Truck + 6 step yaratish."""
    truck = Truck(
        serial_number=serial_number,
        model="Test Model",
        customer="Test Customer",
        priority="normal",
        current_step=1,
        status="in_progress",
        source="admin",
    )
    session.add(truck)
    await session.flush()

    for step_num in range(1, TOTAL_STEPS + 1):
        step = TruckStep(
            truck_id=truck.id,
            step_number=step_num,
            status="pending",
        )
        session.add(step)

    await session.flush()
    return truck


async def submit_step_test(
    session: AsyncSession,
    step: TruckStep,
    worker_id: int,
) -> None:
    """Step yuborish (test uchun — bot siz)."""
    step.worker_id = worker_id
    step.status = "in_review"
    step.media_type = "photo"
    step.media_file_id = "test_file_id"
    step.worker_comment = "Test izoh"
    from datetime import UTC, datetime
    step.submitted_at = datetime.now(UTC)
    await session.flush()


# ==================== E2E TESTLAR ====================

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_full_truck_workflow(session: AsyncSession):
    """To'liq oqim: truck yaratish → 6 step → completed."""
    # 1. Foydalanuvchilar yaratish
    admin = await create_admin(session, 700000001)
    qc = await create_qc(session, 700000002)

    workers = {}
    for step_num in range(1, TOTAL_STEPS + 1):
        workers[step_num] = await create_worker(
            session, step_num, 700000010 + step_num
        )

    # 2. Truck yaratish
    truck = await create_truck_with_steps(session, "TR-E2E-001")

    assert truck.current_step == 1
    assert truck.status == "in_progress"
    assert truck.is_completed is False

    # 3. Har bir step uchun: worker yuboradi → QC tasdiqlaydi
    for step_num in range(1, TOTAL_STEPS + 1):
        worker = workers[step_num]

        # Step ni olish
        stmt = select(TruckStep).where(
            TruckStep.truck_id == truck.id,
            TruckStep.step_number == step_num,
        )
        result = await session.execute(stmt)
        step = result.scalar_one()

        # Worker step ni oladi va yuboradi
        await claim_step(session, step, worker.id)
        await submit_step_test(session, step, worker.id)

        # Tekshirish: step in_review
        assert step.status == "in_review"
        assert step.worker_id == worker.id

        # QC tasdiqlaydi (bot siz — None beramiz, chunki bot kerak emas)
        truck = await approve_step(session, step, qc.id, bot=None)  # type: ignore

        # Tekshirish
        assert step.status == "approved"
        assert step.qc_id == qc.id

        if step_num < TOTAL_STEPS:
            # Keyingi stepga o'tdi
            assert truck.current_step == step_num + 1
            assert truck.status == "in_progress"
        else:
            # Oxirgi step — truck tayyor
            assert truck.status == "completed"
            assert truck.is_completed is True

    # 4. Yakuniy tekshirish
    assert truck.current_step == TOTAL_STEPS
    assert truck.status == "completed"
    assert truck.completed_at is not None

    # 5. Barcha steplar tasdiqlangan
    stmt = select(TruckStep).where(TruckStep.truck_id == truck.id)
    result = await session.execute(stmt)
    all_steps = list(result.scalars().all())

    assert len(all_steps) == TOTAL_STEPS
    for step in all_steps:
        assert step.status == "approved"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_reject_and_resubmit_workflow(session: AsyncSession):
    """Rad etish va qayta yuborish oqimi."""
    # 1. Foydalanuvchilar
    qc = await create_qc(session, 800000001)
    worker = await create_worker(session, 1, 800000010)

    # 2. Truck
    truck = await create_truck_with_steps(session, "TR-E2E-002")

    # 3. Step 1 ni olish
    stmt = select(TruckStep).where(
        TruckStep.truck_id == truck.id,
        TruckStep.step_number == 1,
    )
    result = await session.execute(stmt)
    step = result.scalar_one()

    # 4. Worker yuboradi
    await claim_step(session, step, worker.id)
    await submit_step_test(session, step, worker.id)

    assert step.status == "in_review"

    # 5. QC rad etadi
    await reject_step(
        session, step, qc.id,
        reason="Rasm sifati past",
        bot=None,  # type: ignore
    )

    # 6. Tekshirish
    assert step.status == "rejected"
    assert step.qc_id == qc.id
    assert step.qc_comment == "Rasm sifati past"
    assert step.reviewed_at is not None

    # Truck current_step o'zgarmadi
    assert truck.current_step == 1
    assert truck.status == "in_progress"

    # 7. Worker qayta yuboradi
    await submit_step_test(session, step, worker.id)

    assert step.status == "in_review"

    # 8. QC tasdiqlaydi
    truck = await approve_step(session, step, qc.id, bot=None)  # type: ignore

    assert step.status == "approved"
    assert truck.current_step == 2


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_worker_tasks_appear_and_disappear(session: AsyncSession):
    """Ishchi vazifalari paydo bo'ladi va yo'qoladi."""
    # 1. Foydalanuvchilar
    qc = await create_qc(session, 900000001)
    worker = await create_worker(session, 1, 900000010)

    # 2. Truck
    truck = await create_truck_with_steps(session, "TR-E2E-003")

    # 3. Worker vazifalarni ko'radi
    tasks = await get_worker_tasks(session, worker.id, 1)
    assert len(tasks) == 1
    assert tasks[0].truck_id == truck.id

    # 4. Worker step ni yuboradi
    step = tasks[0]
    await claim_step(session, step, worker.id)
    await submit_step_test(session, step, worker.id)

    # 5. Worker vazifalarni endi ko'rmaydi (status in_review)
    tasks = await get_worker_tasks(session, worker.id, 1)
    assert len(tasks) == 0

    # 6. QC rad etadi
    await reject_step(
        session, step, qc.id,
        reason="Qayta yuboring",
        bot=None,  # type: ignore
    )

    # 7. Worker yana ko'radi (status rejected)
    tasks = await get_worker_tasks(session, worker.id, 1)
    assert len(tasks) == 1

    # 8. QC tasdiqlaydi (qayta yuborgandan keyin)
    await submit_step_test(session, step, worker.id)
    await approve_step(session, step, qc.id, bot=None)  # type: ignore

    # 9. Worker vazifalarni ko'rmaydi (approved, current_step = 2)
    tasks = await get_worker_tasks(session, worker.id, 1)
    assert len(tasks) == 0


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_priority_ordering(session: AsyncSession):
    """Prioritet bo'yicha tartiblash."""
    # 1. Ishchi
    worker = await create_worker(session, 1, 1100000010)

    # 2. 3 ta truck — turli prioritet bilan
    truck_normal = await create_truck_with_steps(session, "TR-NORMAL")
    truck_normal.priority = "normal"

    truck_urgent = await create_truck_with_steps(session, "TR-URGENT")
    truck_urgent.priority = "urgent"

    truck_high = await create_truck_with_steps(session, "TR-HIGH")
    truck_high.priority = "high"

    await session.flush()

    # 3. Worker vazifalarni oladi
    tasks = await get_worker_tasks(session, worker.id, 1)

    # 4. Tartibni tekshirish: urgent → high → normal
    assert len(tasks) == 3
    assert tasks[0].truck.priority == "urgent"
    assert tasks[1].truck.priority == "high"
    assert tasks[2].truck.priority == "normal"
