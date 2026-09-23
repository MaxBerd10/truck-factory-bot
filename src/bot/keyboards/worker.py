"""Worker uchun keyboard lar."""
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database.models.truck_step import TruckStep
from src.utils.constants import (
    STEP_SHORT_NAMES,
)


def worker_tasks_keyboard(tasks: list[TruckStep]):
    """Ishchining vazifalari uchun keyboard."""
    builder = InlineKeyboardBuilder()

    for step in tasks:
        truck = step.truck

        # Priority icon
        priority_icon = {
            "low": "🟢",
            "normal": "🔵",
            "high": "🟠",
            "urgent": "🔴",
        }.get(truck.priority, "⚪")

        # Status icon
        if step.is_rejected:
            status_text = "❌ Qaytarilgan"
        else:
            status_text = "⏳ Yangi"

        builder.button(
            text=f"{priority_icon} {truck.serial_number} — {status_text}",
            callback_data=f"worker_task:{step.id}",
        )

    builder.adjust(1)

    builder.row(
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="worker_refresh"),
        InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu"),
    )

    return builder.as_markup()


def worker_task_detail_keyboard(step: TruckStep):
    """Bitta vazifa tafsiloti uchun keyboard."""
    builder = InlineKeyboardBuilder()

    # Agar rejected bo'lsa — tahrirlash
    if step.is_rejected:
        builder.button(
            text="✏️ Qayta yuborish",
            callback_data=f"worker_submit:{step.id}",
        )
    else:
        # Yangi ish
        builder.button(
            text="📤 Ish yuborish",
            callback_data=f"worker_submit:{step.id}",
        )

    builder.button(
        text="🔙 Vazifalarimga",
        callback_data="worker_refresh",
    )

    builder.adjust(1, 1)
    return builder.as_markup()


def worker_submit_cancel_keyboard():
    """Yuborishni bekor qilish."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="worker_submit_cancel")
    return builder.as_markup()


def worker_submit_skip_comment_keyboard():
    """Izohni o'tkazib yuborish."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⏭ Izohsiz yuborish",
        callback_data="worker_submit_skip_comment",
    )
    builder.button(text="❌ Bekor qilish", callback_data="worker_submit_cancel")
    builder.adjust(2)
    return builder.as_markup()


def worker_submit_confirm_keyboard():
    """Tasdiqlash."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yuborish", callback_data="worker_submit_confirm")
    builder.button(text="✏️ Qaytadan", callback_data="worker_submit_restart")
    builder.button(text="❌ Bekor qilish", callback_data="worker_submit_cancel")
    builder.adjust(2, 1)
    return builder.as_markup()


def worker_history_keyboard(history: list[TruckStep], back: bool = True):
    """Tarix uchun keyboard."""
    builder = InlineKeyboardBuilder()

    for step in history:
        truck = step.truck

        # Status icon
        status_icon = {
            "in_review": "🔍",
            "approved": "✅",
            "rejected": "❌",
        }.get(step.status, "❓")

        step_name = STEP_SHORT_NAMES.get(step.step_number, f"Step {step.step_number}")

        builder.button(
            text=f"{status_icon} {truck.serial_number} — {step_name}",
            callback_data=f"worker_history_view:{step.id}",
        )

    builder.adjust(1)

    if back:
        builder.row(
            InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu"),
        )

    return builder.as_markup()


def worker_history_detail_keyboard(step: TruckStep):
    """Tarix tafsiloti uchun keyboard."""
    builder = InlineKeyboardBuilder()

    if step.is_rejected:
        builder.button(
            text="✏️ Qayta yuborish",
            callback_data=f"worker_submit:{step.id}",
        )

    builder.button(
        text="🔙 Tarixga",
        callback_data="worker_history",
    )

    builder.adjust(1, 1)
    return builder.as_markup()



def worker_after_submit_keyboard():
    """Ish yuborilgandan keyin tugmalar."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Vazifalarimga", callback_data="worker_refresh")
    builder.button(text="🔙 Asosiy menyu", callback_data="main_menu")
    builder.adjust(2)
    return builder.as_markup()
