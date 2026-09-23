"""Foydalanuvchi sozlamalari."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.language import language_settings_keyboard
from src.bot.keyboards.notification import notification_settings_keyboard
from src.database.models.notification import NotificationSettings
from src.database.models.user import User
from src.services.i18n_service import _


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


# ==== "🔔 Sozlamalar" (barcha tillarda) ====
@router.message(
    F.text.in_({
        "🔔 Sozlamalar",   # uz
        "🔔 Созламалар",   # uz_cyrl
        "🔔 Настройки",    # ru
    })
)
async def show_settings(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """Sozlamalarni ko'rsatish."""
    settings = await _get_or_create_settings(session, user.id)

    lang = user.language or "uz"

    text = (
        f"{_('settings.title', language=lang)}\n\n"
        f"{_('settings.notifications', language=lang)}\n\n"
        f"{_('settings.notifications_prompt', language=lang)}"
    )

    await message.answer(
        text,
        reply_markup=notification_settings_keyboard(settings, lang),
    )


# ==== Bildirishnomani yoqish/o'chirish ====
@router.callback_query(F.data.startswith("notif_toggle:"))
async def toggle_notification(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Bildirishnomani yoqish/o'chirish."""
    field = callback.data.split(":")[1]
    lang = user.language or "uz"

    settings = await _get_or_create_settings(session, user.id)

    if not hasattr(settings, field):
        await callback.answer(
            _("common.error_generic", language=lang),
            show_alert=True,
        )
        return

    current = getattr(settings, field)
    setattr(settings, field, not current)
    await session.flush()

    field_key = f"settings.{field}"
    name = _(field_key, language=lang)

    if not current:
        status = _("settings.enabled", language=lang, name=name)
    else:
        status = _("settings.disabled", language=lang, name=name)

    await callback.answer(status)

    try:
        await callback.message.edit_reply_markup(
            reply_markup=notification_settings_keyboard(settings, lang),
        )
    except Exception:
        pass


# ==== "🌐 Tilni o'zgartirish" ====
@router.callback_query(F.data == "settings_language")
async def show_language_settings(
    callback: CallbackQuery,
    user: User,
):
    """Til tanlash (sozlamalarda)."""
    await callback.answer()

    lang = user.language or "uz"

    await callback.message.edit_text(
        f"{_('language.title', language=lang)}\n\n"
        f"{_('language.choose', language=lang)}",
        reply_markup=language_settings_keyboard(),
    )
