"""Bildirishnoma sozlamalari keyboard."""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database.models.notification import NotificationSettings


def notification_settings_keyboard(
    settings: NotificationSettings,
) -> InlineKeyboardMarkup:
    """Bildirishnoma sozlamalari keyboard i."""
    builder = InlineKeyboardBuilder()

    def icon(val: bool) -> str:
        return "✅" if val else "❌"

    builder.button(
        text=f"{icon(settings.on_new_task)} Yangi vazifa",
        callback_data="notif_toggle:on_new_task",
    )
    builder.button(
        text=f"{icon(settings.on_approved)} Tasdiqlanganda",
        callback_data="notif_toggle:on_approved",
    )
    builder.button(
        text=f"{icon(settings.on_rejected)} Rad etilganda",
        callback_data="notif_toggle:on_rejected",
    )
    builder.button(
        text=f"{icon(settings.on_next_step)} Keyingi step",
        callback_data="notif_toggle:on_next_step",
    )
    builder.button(
        text=f"{icon(settings.daily_report)} Kunlik hisobot",
        callback_data="notif_toggle:daily_report",
    )
    builder.button(text="🔙 Orqaga", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()
