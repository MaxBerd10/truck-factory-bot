"""Worker uchun keyboard lar (i18n bilan)."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database.models.truck_step import TruckStep
from src.services.i18n_service import _, get_step_name


def worker_tasks_keyboard(
    tasks: list[TruckStep],
    language: str = "uz",
) -> InlineKeyboardMarkup:
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

        # Status text (qisqa)
        if step.is_rejected:
            status_text = "❌"
        else:
            status_text = "⏳"

        builder.button(
            text=f"{priority_icon} {truck.serial_number} — {status_text}",
            callback_data=f"worker_task:{step.id}",
        )

    builder.adjust(1)

    builder.row(
        InlineKeyboardButton(
            text=f"🔄 {_('common.retry', language=language)}",
            callback_data="worker_refresh",
        ),
        InlineKeyboardButton(
            text=f"🔙 {_('common.main_menu', language=language)}",
            callback_data="main_menu",
        ),
    )

    return builder.as_markup()


def worker_task_detail_keyboard(
    step: TruckStep,
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Bitta vazifa tafsiloti uchun keyboard."""
    builder = InlineKeyboardBuilder()

    if step.is_rejected:
        builder.button(
            text=f"✏️ {_('worker.submit_title', language=language)}",
            callback_data=f"worker_submit:{step.id}",
        )
    else:
        builder.button(
            text=f"📤 {_('worker.menu_submit', language=language)}",
            callback_data=f"worker_submit:{step.id}",
        )

    builder.button(
        text=f"🔙 {_('worker.menu_tasks', language=language)}",
        callback_data="worker_refresh",
    )

    builder.adjust(1, 1)
    return builder.as_markup()


def worker_submit_cancel_keyboard(
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Yuborishni bekor qilish."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="worker_submit_cancel",
    )
    return builder.as_markup()


def worker_submit_skip_comment_keyboard(
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Izohni o'tkazib yuborish."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"⏭ {_('common.skip', language=language)}",
        callback_data="worker_submit_skip_comment",
    )
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="worker_submit_cancel",
    )
    builder.adjust(2)
    return builder.as_markup()


def worker_submit_confirm_keyboard(
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Tasdiqlash."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"✅ {_('common.confirm', language=language)}",
        callback_data="worker_submit_confirm",
    )
    builder.button(
        text=f"✏️ {_('common.retry', language=language)}",
        callback_data="worker_submit_restart",
    )
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="worker_submit_cancel",
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def worker_history_keyboard(
    history: list[TruckStep],
    language: str = "uz",
    back: bool = True,
) -> InlineKeyboardMarkup:
    """Tarix uchun keyboard."""
    builder = InlineKeyboardBuilder()

    for step in history:
        truck = step.truck

        status_icon = {
            "in_review": "🔍",
            "approved": "✅",
            "rejected": "❌",
        }.get(step.status, "❓")

        step_name = get_step_name(step.step_number, language)

        builder.button(
            text=f"{status_icon} {truck.serial_number} — {step_name}",
            callback_data=f"worker_history_view:{step.id}",
        )

    builder.adjust(1)

    if back:
        builder.row(
            InlineKeyboardButton(
                text=f"🔙 {_('common.main_menu', language=language)}",
                callback_data="main_menu",
            ),
        )

    return builder.as_markup()


def worker_history_detail_keyboard(
    step: TruckStep,
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Tarix tafsiloti uchun keyboard."""
    builder = InlineKeyboardBuilder()

    if step.is_rejected:
        builder.button(
            text=f"✏️ {_('worker.submit_title', language=language)}",
            callback_data=f"worker_submit:{step.id}",
        )

    builder.button(
        text=f"🔙 {_('worker.history_title', language=language)}",
        callback_data="worker_history",
    )

    builder.adjust(1, 1)
    return builder.as_markup()


def worker_after_submit_keyboard(
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Ish yuborilgandan keyin tugmalar."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"📋 {_('worker.menu_tasks', language=language)}",
        callback_data="worker_refresh",
    )
    builder.button(
        text=f"🔙 {_('common.main_menu', language=language)}",
        callback_data="main_menu",
    )
    builder.adjust(2)
    return builder.as_markup()
