"""Kunlik hisobot servisi."""
from datetime import UTC, datetime, timedelta

from aiogram import Bot
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.truck import Truck
from src.database.models.truck_step import TruckStep
from src.database.models.user import User
from src.utils.logger import logger


async def get_daily_summary(session: AsyncSession) -> dict:
    """Bugungi kunlik statistika.

    Returns:
        dict: {
            "date": "2026-09-22",
            "trucks_created": int,
            "trucks_completed": int,
            "steps_submitted": int,
            "steps_approved": int,
            "steps_rejected": int,
        }
    """
    today_start = datetime.now(UTC).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_end = today_start + timedelta(days=1)

    # Bugun yaratilgan trucklar
    trucks_created = (
        await session.execute(
            select(func.count(Truck.id)).where(
                Truck.created_at >= today_start,
                Truck.created_at < today_end,
            )
        )
    ).scalar() or 0

    # Bugun tugatilgan trucklar
    trucks_completed = (
        await session.execute(
            select(func.count(Truck.id)).where(
                Truck.completed_at >= today_start,
                Truck.completed_at < today_end,
            )
        )
    ).scalar() or 0

    # Bugun yuborilgan steplar
    steps_submitted = (
        await session.execute(
            select(func.count(TruckStep.id)).where(
                TruckStep.submitted_at >= today_start,
                TruckStep.submitted_at < today_end,
            )
        )
    ).scalar() or 0

    # Bugun tasdiqlangan
    steps_approved = (
        await session.execute(
            select(func.count(TruckStep.id)).where(
                TruckStep.reviewed_at >= today_start,
                TruckStep.reviewed_at < today_end,
                TruckStep.status == "approved",
            )
        )
    ).scalar() or 0

    # Bugun rad etilgan
    steps_rejected = (
        await session.execute(
            select(func.count(TruckStep.id)).where(
                TruckStep.reviewed_at >= today_start,
                TruckStep.reviewed_at < today_end,
                TruckStep.status == "rejected",
            )
        )
    ).scalar() or 0

    return {
        "date": today_start.strftime("%Y-%m-%d"),
        "trucks_created": trucks_created,
        "trucks_completed": trucks_completed,
        "steps_submitted": steps_submitted,
        "steps_approved": steps_approved,
        "steps_rejected": steps_rejected,
    }


async def send_daily_report(
    session: AsyncSession,
    bot: Bot,
    admin_ids: list[int],
) -> None:
    """Kunlik hisobotni adminlarga yuborish."""
    summary = await get_daily_summary(session)

    text = (
        f"📅 <b>Kunlik hisobot</b>\n"
        f"📆 {summary['date']}\n\n"
        f"🚛 <b>Trucklar:</b>\n"
        f"  • Yangi: <b>{summary['trucks_created']}</b>\n"
        f"  • Tugatilgan: <b>{summary['trucks_completed']}</b>\n\n"
        f"🔧 <b>Steplar:</b>\n"
        f"  • Yuborilgan: <b>{summary['steps_submitted']}</b>\n"
        f"  • ✅ Tasdiqlangan: <b>{summary['steps_approved']}</b>\n"
        f"  • ❌ Rad etilgan: <b>{summary['steps_rejected']}</b>\n"
    )

    # Faollik darajasi
    total_actions = summary["steps_approved"] + summary["steps_rejected"]
    if total_actions == 0:
        text += "\n💤 <i>Bugun hech qanday harakat bo'lmadi.</i>"
    elif total_actions < 5:
        text += "\n🟡 <i>O'rtacha faollik.</i>"
    else:
        text += "\n🟢 <i>Yuqori faollik!</i>"

    sent = 0
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, text)
            sent += 1
        except Exception as e:
            logger.warning(f"⚠️ Admin {admin_id} ga yuborilmadi: {e}")

    logger.info(f"📅 Kunlik hisobot yuborildi: {sent}/{len(admin_ids)} admin")


async def get_all_admin_telegram_ids(session: AsyncSession) -> list[int]:
    """Barcha adminlarning telegram_id larini olish."""
    stmt = select(User.telegram_id).where(
        User.role == "admin",
        User.is_active == True,  # noqa: E712
    )
    result = await session.execute(stmt)
    return [row[0] for row in result if row[0]]
