"""Admin — Ishchi reytingi."""
from aiogram import Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsAdmin, text_key
from src.database.models.user import User
from src.services.i18n_service import _, get_step_name
from src.services.rating_service import get_top_workers


router = Router(name="admin_rating")


@router.message(IsAdmin(), text_key("admin.menu_rating"))
async def show_rating(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """TOP ishchilar reytingini ko'rsatish."""
    lang = user.language or "uz"
    workers = await get_top_workers(session, limit=10)

    if not workers:
        await message.answer(
            _("admin.rating_empty", language=lang),
        )
        return

    text = f"{_('admin.rating_title', language=lang)}\n\n"

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    for idx, worker in enumerate(workers, start=1):
        medal = medals.get(idx, f"{idx}.")

        step_info = ""
        if worker["step_number"]:
            step_name = get_step_name(worker["step_number"], lang)
            step_info = f" ({step_name})"

        text += (
            f"{medal} <b>{worker['full_name']}</b>{step_info}\n"
            f"   ✅ {worker['approved']} | "
            f"❌ {worker['rejected']} | "
            f"📊 {worker['success_rate']}%\n\n"
        )

    text += "━━━━━━━━━━━━━━━━━━\n"
    text += _("admin.rating_hint", language=lang)

    await message.answer(text)
