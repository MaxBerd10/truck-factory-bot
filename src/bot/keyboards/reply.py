"""Reply keyboard lar (pastdagi tugmalar)."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from src.utils.constants import (
    ROLE_NAMES,
    STEP_NAMES,
    UserRole,
)


# ==== Umumiy ====
BTN_BACK = "🔙 Orqaga"
BTN_MAIN_MENU = "🏠 Asosiy menyu"
BTN_CANCEL = "❌ Bekor qilish"


def main_menu_keyboard(role: str) -> ReplyKeyboardMarkup:
    """Rolga qarab asosiy menyu."""
    if role == UserRole.WORKER.value:
        return worker_main_menu()
    if role == UserRole.QC.value:
        return qc_main_menu()
    if role == UserRole.ADMIN.value:
        return admin_main_menu()
    return start_keyboard()


def start_keyboard() -> ReplyKeyboardMarkup:
    """Boshlang'ich keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Boshlash")]],
        resize_keyboard=True,
    )


def worker_main_menu() -> ReplyKeyboardMarkup:
    """Ishchi uchun asosiy menyu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Mening vazifalarim")],
            [KeyboardButton(text="📤 Ish yuborish")],
            [KeyboardButton(text="📜 Tarixim")],
        ],
        resize_keyboard=True,
    )


def qc_main_menu() -> ReplyKeyboardMarkup:
    """QC uchun asosiy menyu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔔 Tekshirish navbati")],
            [KeyboardButton(text="📜 Tarixim")],
        ],
        resize_keyboard=True,
    )


def admin_main_menu() -> ReplyKeyboardMarkup:
    """Admin uchun asosiy menyu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Foydalanuvchilar"), KeyboardButton(text="🔗 Invite linklar")],
            [KeyboardButton(text="🚛 Trucklar"), KeyboardButton(text="📊 Statistika")],
        ],
        resize_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Bekor qilish uchun keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
    )
