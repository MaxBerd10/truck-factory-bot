"""Foydalanuvchi sozlamalari."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.notification import notification_settings_keyboard
from src.database.models.notification import NotificationSettings
from src.database.models.user import User


router = Router(name="settings")


async def _get_or_create_settings(
    session: AsyncSession,
    user_id: int,
) -> NotificationSettings:
    """Sozlamalarni olish yoki yaratish."""
    stmt = select(NotificationSettings).where(
        NotificationSettings.user_id == user_id
    )
    result = await session.execute(stmt)
    settings = result.scalar_one_or_none()

    if not settings:
        settings = NotificationSettings(user_id=user_id)
        session.add(settings)
        await session.flush()

    return settings


@router.message(F.text == "🔔 Sozlamalar")
async def show_settings(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """Sozlamalarni ko'rsatish."""
    settings = await _get_or_create_settings(session, user.id)

    text = (
        "🔔 <b>Bildirishnoma sozlamalari</b>\n\n"
        "Qaysi bildirishnomalarni olishni xohlaysiz?\n\n"
        "👇 Tugmalarni bosib yoqing/o'chiring:"
    )

    await message.answer(
        text,
        reply_markup=notification_settings_keyboard(settings),
    )


@router.callback_query(F.data.startswith("notif_toggle:"))
async def toggle_notification(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Bildirishnomani yoqish/o'chirish."""
    field = callback.data.split(":")[1]

    settings = await _get_or_create_settings(session, user.id)

    if not hasattr(settings, field):
        await callback.answer("❌ Xato", show_alert=True)
        return

    current = getattr(settings, field)
    setattr(settings, field, not current)
    await session.flush()

    field_names = {
        "on_new_task": "Yangi vazifa",
        "on_approved": "Tasdiqlanganda",
        "on_rejected": "Rad etilganda",
        "on_next_step": "Keyingi step",
        "daily_report": "Kunlik hisobot",
    }
    name = field_names.get(field, field)

    status = "✅ yoqildi" if not current else "❌ o'chirildi"
    await callback.answer(f"{name}: {status}")

    try:
        await callback.message.edit_reply_markup(
            reply_markup=notification_settings_keyboard(settings),
        )
    except Exception:
        pass
