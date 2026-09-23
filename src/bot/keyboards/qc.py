"""QC uchun keyboard lar (i18n bilan)."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database.models.truck_step import TruckStep
from src.services.i18n_service import _, get_step_name


def qc_queue_keyboard(
    steps: list[TruckStep],
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """QC navbati keyboard i."""
    builder = InlineKeyboardBuilder()

    for step in steps:
        truck = step.truck
        priority_icon = {
            "low": "🟢",
            "normal": "🔵",
            "high": "🟠",
            "urgent": "🔴",
        }.get(truck.priority, "⚪")

        step_name = get_step_name(step.step_number, language)

        builder.button(
            text=f"{priority_icon} {truck.serial_number} — {step_name}",
            callback_data=f"qc_view:{step.id}",
        )

    builder.adjust(1)

    builder.row(
        InlineKeyboardButton(
            text=f"🔄 {_('common.retry', language=language)}",
            callback_data="qc_refresh",
        ),
        InlineKeyboardButton(
            text=f"🔙 {_('common.main_menu', language=language)}",
            callback_data="main_menu",
        ),
    )

    return builder.as_markup()


def qc_review_keyboard(
    step_id: int,
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Tekshirish keyboard i."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=f"✅ {_('qc.review_approve_btn', language=language)}",
        callback_data=f"qc_approve:{step_id}",
    )
    builder.button(
        text=f"❌ {_('qc.review_reject_btn', language=language)}",
        callback_data=f"qc_reject:{step_id}",
    )
    builder.button(
        text=f"🔙 {_('common.back', language=language)}",
        callback_data="qc_refresh",
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def qc_approve_confirm_keyboard(
    step_id: int,
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Tasdiqlashni tasdiqlash."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"✅ {_('common.yes', language=language)}",
        callback_data=f"qc_approve_confirm:{step_id}",
    )
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="qc_refresh",
    )
    builder.adjust(2)
    return builder.as_markup()


def qc_reject_cancel_keyboard(
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Rad etishni bekor qilish."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="qc_reject_cancel",
    )
    return builder.as_markup()


def qc_reject_confirm_keyboard(
    step_id: int,
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Rad etishni tasdiqlash."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"✅ {_('common.confirm', language=language)}",
        callback_data=f"qc_reject_confirm:{step_id}",
    )
    builder.button(
        text=f"✏️ {_('common.retry', language=language)}",
        callback_data=f"qc_reject_restart:{step_id}",
    )
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="qc_reject_cancel",
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def qc_after_action_keyboard(
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """QC amaldan keyingi tugmalar."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"🔔 {_('qc.menu_queue', language=language)}",
        callback_data="qc_refresh",
    )
    builder.button(
        text=f"📊 {_('qc.menu_stats', language=language)}",
        callback_data="qc_stats_view",
    )
    builder.button(
        text=f"🏠 {_('common.main_menu', language=language)}",
        callback_data="main_menu",
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def qc_history_keyboard(
    history: list[TruckStep],
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Tarix keyboard i."""
    builder = InlineKeyboardBuilder()

    for step in history:
        truck = step.truck

        status_icon = {
            "approved": "✅",
            "rejected": "❌",
        }.get(step.status, "❓")

        step_name = get_step_name(step.step_number, language)

        builder.button(
            text=f"{status_icon} {truck.serial_number} — {step_name}",
            callback_data=f"qc_history_view:{step.id}",
        )

    builder.adjust(1)

    builder.row(
        InlineKeyboardButton(
            text=f"🔙 {_('common.main_menu', language=language)}",
            callback_data="main_menu",
        ),
    )

    return builder.as_markup()


def qc_history_detail_keyboard(
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Tarix tafsiloti keyboard i."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"🔙 {_('qc.history_title', language=language)}",
        callback_data="qc_history",
    )
    return builder.as_markup()
