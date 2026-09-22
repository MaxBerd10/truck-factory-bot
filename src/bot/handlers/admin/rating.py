"""Admin — Ishchi reytingi."""
from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsAdmin
from src.services.rating_service import get_top_workers
from src.utils.constants import STEP_NAMES


router = Router(name="admin_rating")


@router.message(IsAdmin(), F.text == "🏆 Reyting")
async def show_rating(
    message: Message,
    session: AsyncSession,
):
    """TOP ishchilar reytingini ko'rsatish."""
    workers = await get_top_workers(session, limit=10)

    if not workers:
        await message.answer(
            "🏆 <b>Ishchi reytingi</b>\n\n"
            "📋 Hozircha ma'lumot yo'q.\n\n"
            "💡 Ishchilar ish yuborgandan keyin reyting paydo bo'ladi.",
        )
        return

    text = "🏆 <b>TOP ishchilar</b>\n\n"

    # Medal ikonkalari
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    for idx, worker in enumerate(workers, start=1):
        medal = medals.get(idx, f"{idx}.")

        step_info = ""
        if worker["step_number"]:
            step_name = STEP_NAMES.get(
                worker["step_number"], f"Step {worker['step_number']}"
            )
            step_info = f" ({step_name})"

        text += (
            f"{medal} <b>{worker['full_name']}</b>{step_info}\n"
            f"   ✅ {worker['approved']} | "
            f"❌ {worker['rejected']} | "
            f"📊 {worker['success_rate']}%\n\n"
        )

    text += "━━━━━━━━━━━━━━━━━━\n"
    text += "💡 <i>Reyting tasdiqlangan ishlar soni bo'yicha.</i>"

    await message.answer(text)
