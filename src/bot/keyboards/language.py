"""Til tanlash keyboard."""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def language_keyboard() -> InlineKeyboardMarkup:
    """Til tanlash keyboard i."""
    builder = InlineKeyboardBuilder()

    builder.button(text="🇺🇿 O'zbekcha", callback_data="lang:uz")
    builder.button(text="🇺🇿 Ўзбекча", callback_data="lang:uz_cyrl")
    builder.button(text="🇷🇺 Русский", callback_data="lang:ru")

    builder.adjust(1)
    return builder.as_markup()


def language_settings_keyboard() -> InlineKeyboardMarkup:
    """Sozlamalardagi til keyboard i."""
    builder = InlineKeyboardBuilder()

    builder.button(text="🇺🇿 O'zbekcha", callback_data="lang_set:uz")
    builder.button(text="🇺🇿 Ўзбекча", callback_data="lang_set:uz_cyrl")
    builder.button(text="🇷🇺 Русский", callback_data="lang_set:ru")
    builder.button(text="🔙 Orqaga", callback_data="main_menu")

    builder.adjust(1)
    return builder.as_markup()
