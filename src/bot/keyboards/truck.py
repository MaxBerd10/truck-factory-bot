"""Truck uchun keyboard lar."""
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database.models.truck import Truck
from src.utils.constants import (
    PRIORITY_NAMES,
    STATUS_NAMES,
    STEP_SHORT_NAMES,
)


def trucks_list_keyboard(
    trucks: list[Truck],
    page: int = 0,
    per_page: int = 10,
    total: int = 0,
):
    """Trucklar ro'yxati uchun keyboard."""
    builder = InlineKeyboardBuilder()

    for truck in trucks:
        # Priority icon
        priority_icon = {
            "low": "🟢",
            "normal": "🔵",
            "high": "🟠",
            "urgent": "🔴",
        }.get(truck.priority, "⚪")

        # Status
        if truck.is_completed:
            status_icon = "✅"
        else:
            status_icon = f"{truck.current_step}/6"

        builder.button(
            text=f"{priority_icon} {truck.serial_number} — {status_icon}",
            callback_data=f"truck_view:{truck.id}",
        )

    builder.adjust(1)

    # ==== Navigatsiya ====
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Oldingi",
                callback_data=f"trucks_page:{page - 1}",
            )
        )
    if total > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text=f"📄 {page + 1}/{total_pages}",
                callback_data="noop",
            )
        )
    if (page + 1) * per_page < total:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Keyingi ➡️",
                callback_data=f"trucks_page:{page + 1}",
            )
        )

    # Amallar
    builder.row(
        InlineKeyboardButton(text="➕ Yangi truck", callback_data="truck_add"),
        InlineKeyboardButton(
            text="🔄 Yangilash",
            callback_data=f"trucks_page:{page}",
        ),
    )

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu"),
    )

    return builder.as_markup()


def truck_detail_keyboard(truck: Truck, back_page: int = 0):
    """Bitta truck tafsilotlari uchun keyboard."""
    builder = InlineKeyboardBuilder()

    # O'chirish
    builder.button(
        text="🗑 O'chirish",
        callback_data=f"truck_delete:{truck.id}",
    )

    # Orqaga
    builder.button(
        text="🔙 Ro'yxatga",
        callback_data=f"trucks_page:{back_page}",
    )

    builder.adjust(1, 1)
    return builder.as_markup()


def truck_priority_keyboard():
    """Priority tanlash."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🟢 Past", callback_data="truck_priority:low")
    builder.button(text="🔵 Oddiy", callback_data="truck_priority:normal")
    builder.button(text="🟠 Yuqori", callback_data="truck_priority:high")
    builder.button(text="🔴 Shoshilinch", callback_data="truck_priority:urgent")
    builder.button(text="❌ Bekor qilish", callback_data="truck_cancel")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def truck_skip_keyboard(skip_field: str = "customer"):
    """O'tkazib yuborish (customer yoki deadline)."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⏭ O'tkazib yuborish",
        callback_data=f"truck_skip_{skip_field}",
    )
    builder.button(text="❌ Bekor qilish", callback_data="truck_cancel")
    builder.adjust(2)
    return builder.as_markup()


def truck_confirm_keyboard():
    """Tasdiqlash."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yaratish", callback_data="truck_confirm")
    builder.button(text="✏️ Qaytadan", callback_data="truck_restart")
    builder.button(text="❌ Bekor qilish", callback_data="truck_cancel")
    builder.adjust(2, 1)
    return builder.as_markup()
