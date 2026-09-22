"""QC uchun keyboard lar."""
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database.models.truck_step import TruckStep
from src.utils.constants import (
    PRIORITY_NAMES,
    STEP_NAMES,
    STEP_SHORT_NAMES,
)


def qc_queue_keyboard(steps: list[TruckStep]):
    """Tekshirish navbati uchun keyboard."""
    builder = InlineKeyboardBuilder()

    for step in steps:
        truck = step.truck

        priority_icon = {
            "low": "🟢",
            "normal": "🔵",
            "high": "🟠",
            "urgent": "🔴",
        }.get(truck.priority, "⚪")

        step_name = STEP_SHORT_NAMES.get(
            step.step_number, f"Step {step.step_number}"
        )

        builder.button(
            text=f"{priority_icon} {truck.serial_number} — {step_name}",
            callback_data=f"qc_view:{step.id}",
        )

    builder.adjust(1)

    builder.row(
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="qc_refresh"),
        InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu"),
    )

    return builder.as_markup()


def qc_review_keyboard(step_id: int):
    """Tekshirish uchun keyboard."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Tasdiqlash",
        callback_data=f"qc_approve:{step_id}",
    )
    builder.button(
        text="❌ Rad etish",
        callback_data=f"qc_reject:{step_id}",
    )
    builder.button(
        text="🔙 Navbatga",
        callback_data="qc_refresh",
    )

    builder.adjust(2, 1)
    return builder.as_markup()


def qc_approve_confirm_keyboard(step_id: int):
    """Tasdiqlashni confirm qilish."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Ha, tasdiqlash",
        callback_data=f"qc_approve_confirm:{step_id}",
    )
    builder.button(
        text="❌ Yo'q",
        callback_data=f"qc_view:{step_id}",
    )

    builder.adjust(1, 1)
    return builder.as_markup()


def qc_reject_cancel_keyboard():
    """Rad etishni bekor qilish."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="qc_reject_cancel")
    return builder.as_markup()


def qc_reject_confirm_keyboard(step_id: int):
    """Rad etishni confirm qilish."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Rad etish",
        callback_data=f"qc_reject_confirm:{step_id}",
    )
    builder.button(
        text="✏️ Qaytadan",
        callback_data=f"qc_reject_restart:{step_id}",
    )
    builder.button(
        text="❌ Bekor qilish",
        callback_data=f"qc_view:{step_id}",
    )

    builder.adjust(2, 1)
    return builder.as_markup()


def qc_history_keyboard(history: list[TruckStep]):
    """QC tarixi uchun keyboard."""
    builder = InlineKeyboardBuilder()

    for step in history:
        truck = step.truck

        status_icon = {
            "approved": "✅",
            "rejected": "❌",
        }.get(step.status, "❓")

        step_name = STEP_SHORT_NAMES.get(
            step.step_number, f"Step {step.step_number}"
        )

        builder.button(
            text=f"{status_icon} {truck.serial_number} — {step_name}",
            callback_data=f"qc_history_view:{step.id}",
        )

    builder.adjust(1)

    builder.row(
        InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu"),
    )

    return builder.as_markup()


def qc_history_detail_keyboard():
    """QC tarix tafsiloti uchun keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Tarixga", callback_data="qc_history")
    return builder.as_markup()


def qc_after_action_keyboard():
    """QC amaldan keyingi tugmalar (approve/reject dan keyin)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔔 Navbatga qaytish", callback_data="qc_refresh")
    builder.button(text="🔙 Asosiy menyu", callback_data="main_menu")
    builder.adjust(2)
    return builder.as_markup()
