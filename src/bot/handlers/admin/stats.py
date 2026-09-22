"""Admin — Statistika."""
from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsAdmin
from src.services.stats_service import get_admin_stats
from src.utils.constants import STEP_SHORT_NAMES


router = Router(name="admin_stats")


# ==== "Statistika" ====
@router.message(IsAdmin(), F.text == "📊 Statistika")
async def show_stats(
    message: Message,
    session: AsyncSession,
):
    """Statistikani ko'rsatish."""
    stats = await get_admin_stats(session)

    trucks = stats["trucks"]
    steps = stats["steps"]
    users = stats["users"]
    by_step = stats["by_step"]

    text = (
        "📊 <b>Umumiy statistika</b>\n\n"
        "🚛 <b>Trucklar:</b>\n"
        f"  • Jami: <b>{trucks['total']}</b>\n"
        f"  • Jarayonda: <b>{trucks['in_progress']}</b>\n"
        f"  • Tayyor: <b>{trucks['completed']}</b>\n\n"
        "🔧 <b>Steplar:</b>\n"
        f"  • Jami: <b>{steps['total']}</b>\n"
        f"  • ⏳ Kutilmoqda: <b>{steps['pending']}</b>\n"
        f"  • 🔍 Tekshirilmoqda: <b>{steps['in_review']}</b>\n"
        f"  • ✅ Tasdiqlangan: <b>{steps['approved']}</b>\n"
        f"  • ❌ Rad etilgan: <b>{steps['rejected']}</b>\n\n"
        "👥 <b>Foydalanuvchilar:</b>\n"
        f"  • Jami: <b>{users['total']}</b>\n"
        f"  • 👷 Ishchilar: <b>{users['workers']}</b>\n"
        f"  • 🔍 QC: <b>{users['qc']}</b>\n"
        f"  • 👑 Adminlar: <b>{users['admins']}</b>\n"
        f"  • 🚫 Bloklangan: <b>{users['inactive']}</b>\n\n"
    )

    # Har bir step bo'yicha
    text += "📈 <b>Har bir step bo'yicha:</b>\n"
    for step_num in range(1, 7):
        step_name = STEP_SHORT_NAMES.get(step_num, f"Step {step_num}")
        s = by_step[step_num]

        # Faqat noldan katta bo'lganlar
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


from aiogram.types import CallbackQuery
from src.bot.keyboards.admin import export_keyboard


@router.message(IsAdmin(), F.text == "📤 Excel hisobot")
async def show_export_menu(
    message: Message,
):
    """Excel hisobot menyusini ko'rsatish."""
    await message.answer(
        "📤 <b>Excel hisobot</b>\n\n"
        "Qaysi hisobotni yuklab olasiz?\n\n"
        "📊 <b>Trucklar</b> — barcha trucklar ro'yxati\n"
        "✅ <b>Tayyor</b> — faqat tugatilgan trucklar\n"
        "🔵 <b>Jarayonda</b> — hozir ishlanayotgan trucklar\n"
        "📋 <b>Steplar</b> — har bir step bo'yicha batafsil\n\n"
        "💡 <i>Fayl .xlsx formatda yuklab olinadi.</i>",
        reply_markup=export_keyboard(),
    )
