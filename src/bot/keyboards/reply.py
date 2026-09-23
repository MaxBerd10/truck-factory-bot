"""Reply (pastdagi) keyboard lar (i18n bilan)."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from src.services.i18n_service import _


def worker_menu_keyboard(language: str = "uz") -> ReplyKeyboardMarkup:
    """Ishchi uchun asosiy menyu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("worker.menu_tasks", language=language)),
                KeyboardButton(text=_("worker.menu_submit", language=language)),
            ],
            [
                KeyboardButton(text=_("worker.menu_history", language=language)),
                KeyboardButton(text=_("worker.menu_stats", language=language)),
            ],
            [
                KeyboardButton(text=_("settings.title", language=language)),
                KeyboardButton(text=_("common.main_menu", language=language)),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder=_("start.choose_section", language=language),
    )


def qc_menu_keyboard(language: str = "uz") -> ReplyKeyboardMarkup:
    """QC uchun asosiy menyu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("qc.menu_queue", language=language)),
            ],
            [
                KeyboardButton(text=_("qc.menu_history", language=language)),
                KeyboardButton(text=_("qc.menu_stats", language=language)),
            ],
            [
                KeyboardButton(text=_("settings.title", language=language)),
                KeyboardButton(text=_("common.main_menu", language=language)),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder=_("start.choose_section", language=language),
    )


def admin_menu_keyboard(language: str = "uz") -> ReplyKeyboardMarkup:
    """Admin uchun asosiy menyu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("admin.menu_trucks", language=language)),
                KeyboardButton(text=_("admin.menu_users", language=language)),
            ],
            [
                KeyboardButton(text=_("admin.menu_new_truck", language=language)),
                KeyboardButton(text=_("admin.menu_stats", language=language)),
            ],
            [
                KeyboardButton(text=_("admin.menu_rating", language=language)),
                KeyboardButton(text=_("admin.menu_chart", language=language)),
            ],
            [
                KeyboardButton(text=_("admin.menu_excel", language=language)),
                KeyboardButton(text=_("admin.menu_settings", language=language)),
            ],
            [
                KeyboardButton(text=_("common.main_menu", language=language)),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder=_("start.choose_section", language=language),
    )
