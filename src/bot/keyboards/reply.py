"""Reply (pastdagi) keyboard lar."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def worker_menu_keyboard() -> ReplyKeyboardMarkup:
    """Ishchi uchun asosiy menyu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Vazifalarim"),
                KeyboardButton(text="📤 Ish yuborish"),
            ],
            [
                KeyboardButton(text="📜 Tarixim"),
                KeyboardButton(text="📊 Statistika"),
            ],
            [
                KeyboardButton(text="🏠 Asosiy menyu"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Bo'limni tanlang...",
    )


def qc_menu_keyboard() -> ReplyKeyboardMarkup:
    """QC uchun asosiy menyu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔔 Tekshirish navbati"),
            ],
            [
                KeyboardButton(text="📜 Tarixim"),
                KeyboardButton(text="📊 Statistika"),
            ],
            [
                KeyboardButton(text="🏠 Asosiy menyu"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Bo'limni tanlang...",
    )


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Admin uchun asosiy menyu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🚛 Trucklar"),
                KeyboardButton(text="👥 Foydalanuvchilar"),
            ],
            [
                KeyboardButton(text="➕ Yangi truck"),
                KeyboardButton(text="📊 Statistika"),
            ],
            [
                KeyboardButton(text="🏆 Reyting"),
                KeyboardButton(text="📤 Excel hisobot"),
            ],
            [
                KeyboardButton(text="🏠 Asosiy menyu"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Bo'limni tanlang...",
    )
