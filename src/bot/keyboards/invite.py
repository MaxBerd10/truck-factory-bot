"""Invite (taklif) keyboard lar."""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.utils.constants import STEP_NAMES


def invite_role_keyboard() -> InlineKeyboardMarkup:
    """Rol tanlash keyboard i."""
    builder = InlineKeyboardBuilder()
    builder.button(text="👷 Ishchi", callback_data="invite_role:worker")
    builder.button(text="🔍 Sifat nazoratchisi", callback_data="invite_role:qc")
    builder.button(text="👑 Administrator", callback_data="invite_role:admin")
    builder.button(text="❌ Bekor qilish", callback_data="invite_cancel")
    builder.adjust(1)
    return builder.as_markup()


def invite_step_keyboard() -> InlineKeyboardMarkup:
    """Step tanlash keyboard i."""
    builder = InlineKeyboardBuilder()
    for step_num in range(1, 7):
        step_name = STEP_NAMES.get(step_num, f"Step {step_num}")
        builder.button(
            text=f"{step_num}️⃣ {step_name}",
            callback_data=f"invite_step:{step_num}",
        )
    builder.button(text="❌ Bekor qilish", callback_data="invite_cancel")
    builder.adjust(1)
    return builder.as_markup()


def invite_cancel_keyboard() -> InlineKeyboardMarkup:
    """Tasdiqlash keyboard i (invite uchun)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yaratish", callback_data="invite_confirm")
    builder.button(text="❌ Bekor qilish", callback_data="invite_cancel")
    builder.adjust(2)
    return builder.as_markup()
