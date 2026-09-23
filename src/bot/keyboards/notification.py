"""Bildirishnoma sozlamalari keyboard."""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database.models.notification import NotificationSettings
from src.services.i18n_service import _


def notification_settings_keyboard(
    settings: NotificationSettings,
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Bildirishnoma sozlamalari keyboard i."""
    builder = InlineKeyboardBuilder()

    def icon(val: bool) -> str:
        return "✅" if val else "❌"

    builder.button(
        text=f"{icon(settings.on_new_task)} {_('settings.on_new_task', language)}",
        callback_data="notif_toggle:on_new_task",
    )
    builder.button(
        text=f"{icon(settings.on_approved)} {_('settings.on_approved', language)}",
        callback_data="notif_toggle:on_approved",
    )
    builder.button(
        text=f"{icon(settings.on_rejected)} {_('settings.on_rejected', language)}",
        callback_data="notif_toggle:on_rejected",
    )
    builder.button(
        text=f"{icon(settings.on_next_step)} {_('settings.on_next_step', language)}",
        callback_data="notif_toggle:on_next_step",
    )
    builder.button(
        text=f"{icon(settings.daily_report)} {_('settings.daily_report', language)}",
        callback_data="notif_toggle:daily_report",
    )

    # Til o'zgartirish
    builder.button(
        text=_("settings.change_language", language),
        callback_data="settings_language",
    )

    # Asosiy menyu
    builder.button(
        text=f"🔙 {_('common.main_menu', language)}",
        callback_data="main_menu",
    )

    builder.adjust(1)
    return builder.as_markup()
