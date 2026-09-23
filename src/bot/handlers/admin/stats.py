"""Admin — Statistika va grafik."""
from aiogram import Router
from aiogram.types import BufferedInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsAdmin, text_key
from src.database.models.user import User
from src.services.chart_service import generate_monthly_chart
from src.services.i18n_service import _, get_step_name
from src.services.stats_service import get_admin_stats


router = Router(name="admin_stats")


# ==================== "Statistika" ====================
@router.message(IsAdmin(), text_key("admin.menu_stats"))
async def show_stats(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """Statistikani ko'rsatish."""
    lang = user.language or "uz"
    stats = await get_admin_stats(session)

    trucks = stats["trucks"]
    steps = stats["steps"]
    users = stats["users"]
    by_step = stats["by_step"]

    text = f"{_('admin.stats_title', language=lang)}\n\n"
    text += f"{_('admin.stats_trucks', language=lang)}\n"
    text += f"  • {_('admin.stats_total', language=lang, count=trucks['total'])}\n"
    text += f"  • {_('admin.stats_in_progress', language=lang, count=trucks['in_progress'])}\n"
    text += f"  • {_('admin.stats_completed', language=lang, count=trucks['completed'])}\n\n"

    text += f"{_('admin.stats_steps', language=lang)}\n"
    text += f"  • {_('statuses.pending', language=lang)}: {steps['pending']}\n"
    text += f"  • {_('statuses.in_review', language=lang)}: {steps['in_review']}\n"
    text += f"  • {_('statuses.approved', language=lang)}: {steps['approved']}\n"
    text += f"  • {_('statuses.rejected', language=lang)}: {steps['rejected']}\n\n"

    text += f"{_('admin.stats_users', language=lang)}\n"
    text += f"  • {_('admin.stats_total', language=lang, count=users['total'])}\n"
    text += f"  • {_('admin.stats_workers', language=lang, count=users['workers'])}\n"
    text += f"  • {_('admin.stats_qc', language=lang, count=users['qc'])}\n"
    text += f"  • {_('admin.stats_admins', language=lang, count=users['admins'])}\n"
    text += f"  • {_('admin.stats_inactive', language=lang, count=users['inactive'])}\n\n"

    text += f"{_('admin.stats_by_step', language=lang)}\n"

    for step_num in range(1, 7):
        step_name = get_step_name(step_num, lang)
        s = by_step[step_num]

        parts = []
        if s["pending"] > 0:
            parts.append(f"⏳{s['pending']}")
        if s["in_review"] > 0:
            parts.append(f"🔍{s['in_review']}")
        if s["approved"] > 0:
            parts.append(f"✅{s['approved']}")
        if s["rejected"] > 0:
            parts.append(f"❌{s['rejected']}")

        if parts:
            text += f"  • {step_num}. {step_name}: {' '.join(parts)}\n"
        else:
            text += f"  • {step_num}. {step_name}: —\n"

    await message.answer(text)


# ==================== "Grafik" ====================
@router.message(IsAdmin(), text_key("admin.menu_chart"))
async def show_monthly_chart(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """Oylik grafikni ko'rsatish."""
    lang = user.language or "uz"

    await message.answer(
        _("admin.chart_generating", language=lang)
    )

    buf = await generate_monthly_chart(session)

    await message.answer_photo(
        photo=BufferedInputFile(buf.getvalue(), filename="chart.png"),
        caption=_("admin.chart_title", language=lang),
    )
