"""Registration (ro'yxatdan o'tish) keyboard lar."""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def registration_confirm_keyboard() -> InlineKeyboardMarkup:
    """Ro'yxatdan o'tishni tasdiqlash."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data="reg_confirm")
    builder.button(text="❌ Bekor qilish", callback_data="reg_cancel")
    builder.adjust(2)
    return builder.as_markup()


def registration_skip_phone_keyboard() -> InlineKeyboardMarkup:
    """Telefon raqamini o'tkazib yuborish."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⏭ O'tkazib yuborish",
        callback_data="reg_skip_phone",
    )
    builder.button(text="❌ Bekor qilish", callback_data="reg_cancel")
    builder.adjust(2)
    return builder.as_markup()


def registration_cancel_keyboard() -> InlineKeyboardMarkup:
    """Ro'yxatdan o'tishni bekor qilish."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="reg_cancel")
    return builder.as_markup()
