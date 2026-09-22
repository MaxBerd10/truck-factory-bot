"""Ro'yxatdan o'tish uchun keyboard lar."""
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def registration_skip_phone_keyboard():
    """Telefon raqamni o'tkazib yuborish."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⏭ O'tkazib yuborish",
        callback_data="reg_skip_phone",
    )
    builder.button(
        text="❌ Bekor qilish",
        callback_data="reg_cancel",
    )
    builder.adjust(2)
    return builder.as_markup()


def registration_confirm_keyboard():
    """Tasdiqlash."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Tasdiqlash",
        callback_data="reg_confirm",
    )
    builder.button(
        text="✏️ Qaytadan",
        callback_data="reg_restart",
    )
    builder.button(
        text="❌ Bekor qilish",
        callback_data="reg_cancel",
    )
    builder.adjust(2, 1)
    return builder.as_markup()
