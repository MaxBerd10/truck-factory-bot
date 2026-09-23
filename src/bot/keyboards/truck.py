"""Truck uchun keyboard lar (i18n bilan)."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database.models.truck import Truck
from src.services.i18n_service import _


def trucks_list_keyboard(
    trucks: list[Truck],
    page: int = 0,
    per_page: int = 5,
    total: int = 0,
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Trucklar ro'yxati uchun keyboard."""
    builder = InlineKeyboardBuilder()

    for truck in trucks:
        priority_icon = {
            "low": "🟢",
            "normal": "🔵",
            "high": "🟠",
            "urgent": "🔴",
        }.get(truck.priority, "⚪")

        if truck.is_completed:
            status_icon = "✅"
        else:
            status_icon = f"{truck.current_step}/6"

        builder.button(
            text=f"{priority_icon} {truck.serial_number} — {status_icon}",
            callback_data=f"truck_view:{truck.id}",
        )

    builder.adjust(1)

    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text=f"⬅️ {_('common.back', language=language)}",
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
                text=f"{_('common.retry', language=language)} ➡️",
                callback_data=f"trucks_page:{page + 1}",
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=f"➕ {_('admin.menu_new_truck', language=language)}",
            callback_data="truck_add",
        ),
        InlineKeyboardButton(
            text=f"🔄 {_('common.retry', language=language)}",
            callback_data=f"trucks_page:{page}",
        ),
    )

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(
            text=f"🔙 {_('common.main_menu', language=language)}",
            callback_data="main_menu",
        ),
    )

    return builder.as_markup()


def truck_detail_keyboard(
    truck: Truck,
    back_page: int = 0,
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Bitta truck tafsilotlari uchun keyboard."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=f"📅 {_('admin.timeline_title', language=language)}",
        callback_data=f"truck_timeline:{truck.id}",
    )

    builder.button(
        text=f"🗑 {_('common.cancel', language=language)}",
        callback_data=f"truck_delete:{truck.id}",
    )

    builder.button(
        text=f"🔙 {_('common.back', language=language)}",
        callback_data=f"trucks_page:{back_page}",
    )

    builder.adjust(1, 1, 1)
    return builder.as_markup()


def truck_priority_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    """Priority tanlash."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"🟢 {_('priorities.low', language=language)}",
        callback_data="truck_priority:low",
    )
    builder.button(
        text=f"🔵 {_('priorities.normal', language=language)}",
        callback_data="truck_priority:normal",
    )
    builder.button(
        text=f"🟠 {_('priorities.high', language=language)}",
        callback_data="truck_priority:high",
    )
    builder.button(
        text=f"🔴 {_('priorities.urgent', language=language)}",
        callback_data="truck_priority:urgent",
    )
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="truck_cancel",
    )
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def truck_skip_keyboard(
    skip_field: str = "customer",
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """O'tkazib yuborish (customer yoki deadline)."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"⏭ {_('common.skip', language=language)}",
        callback_data=f"truck_skip_{skip_field}",
    )
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="truck_cancel",
    )
    builder.adjust(2)
    return builder.as_markup()


def truck_confirm_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    """Tasdiqlash."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"✅ {_('common.confirm', language=language)}",
        callback_data="truck_confirm",
    )
    builder.button(
        text=f"✏️ {_('common.retry', language=language)}",
        callback_data="truck_restart",
    )
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="truck_cancel",
    )
    builder.adjust(2, 1)
    return builder.as_markup()
