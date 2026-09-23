"""Grafik servisi (matplotlib)."""
from datetime import UTC, datetime, timedelta
from io import BytesIO

import matplotlib


matplotlib.use("Agg")  # GUI siz
import matplotlib.pyplot as plt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.truck_step import TruckStep


# Uslub
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8


async def generate_monthly_chart(session: AsyncSession) -> BytesIO:
    """Oxirgi 30 kunlik statistika grafigi.

    Returns:
        BytesIO: PNG rasm
    """
    # Oxirgi 30 kun
    today = datetime.now(UTC).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start_date = today - timedelta(days=29)

    # Har kun uchun: yuborilgan va tasdiqlangan steplar
    stmt_submitted = (
        select(
            func.date_trunc("day", TruckStep.submitted_at).label("day"),
            func.count(TruckStep.id),
        )
        .where(TruckStep.submitted_at >= start_date)
        .group_by("day")
        .order_by("day")
    )

    stmt_approved = (
        select(
            func.date_trunc("day", TruckStep.reviewed_at).label("day"),
            func.count(TruckStep.id),
        )
        .where(
            TruckStep.reviewed_at >= start_date,
            TruckStep.status == "approved",
        )
        .group_by("day")
        .order_by("day")
    )

    submitted_result = await session.execute(stmt_submitted)
    approved_result = await session.execute(stmt_approved)

    # Dict ga o'tkazish
    submitted_data = {
        row[0].date(): row[1] for row in submitted_result if row[0]
    }
    approved_data = {
        row[0].date(): row[1] for row in approved_result if row[0]
    }

    # 30 kunlik ro'yxat
    days = [(start_date + timedelta(days=i)).date() for i in range(30)]
    submitted_values = [submitted_data.get(d, 0) for d in days]
    approved_values = [approved_data.get(d, 0) for d in days]

    # Grafik
    fig, ax = plt.subplots(figsize=(12, 5), dpi=100)

    x = range(len(days))

    ax.plot(
        x, submitted_values,
        marker="o", linewidth=2, markersize=4,
        color="#4A90E2", label="Yuborilgan",
    )
    ax.plot(
        x, approved_values,
        marker="s", linewidth=2, markersize=4,
        color="#27AE60", label="Tasdiqlangan",
    )

    # X o'qi (har 5 kun)
    tick_positions = list(range(0, len(days), 5))
    tick_labels = [days[i].strftime("%m-%d") for i in tick_positions]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=45)

    ax.set_xlabel("Sana", fontsize=11)
    ax.set_ylabel("Steplar soni", fontsize=11)
    ax.set_title(
        "Oxirgi 30 kunlik statistika",
        fontsize=14, fontweight="bold", pad=15,
    )
    ax.legend(loc="upper left", fontsize=10)
    ax.grid(True, alpha=0.3, linestyle="--")

    plt.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf
