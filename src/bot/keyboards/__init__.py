"""Keyboards."""
from src.bot.keyboards.admin import (
    cancel_add_user_keyboard,
    confirm_add_user_keyboard,
    role_choice_keyboard,
    skip_phone_keyboard,
    step_choice_keyboard,
    user_detail_keyboard,
    users_list_keyboard,
)
from src.bot.keyboards.reply import (
    BTN_BACK,
    BTN_CANCEL,
    BTN_MAIN_MENU,
    admin_main_menu,
    cancel_keyboard,
    main_menu_keyboard,
    qc_main_menu,
    start_keyboard,
    worker_main_menu,
)


__all__ = [
    "BTN_BACK",
    "BTN_CANCEL",
    "BTN_MAIN_MENU",
    "main_menu_keyboard",
    "start_keyboard",
    "worker_main_menu",
    "qc_main_menu",
    "admin_main_menu",
    "cancel_keyboard",
    "users_list_keyboard",
    "user_detail_keyboard",
    "skip_phone_keyboard",
    "cancel_add_user_keyboard",
    "role_choice_keyboard",
    "step_choice_keyboard",
    "confirm_add_user_keyboard",
]
