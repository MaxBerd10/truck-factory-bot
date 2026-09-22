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
from src.bot.keyboards.invite import (
    invite_confirm_keyboard,
    invite_detail_keyboard,
    invite_expires_keyboard,
    invite_max_uses_keyboard,
    invite_role_keyboard,
    invite_step_keyboard,
    invites_list_keyboard,
)
from src.bot.keyboards.registration import (
    registration_confirm_keyboard,
    registration_skip_phone_keyboard,
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
from src.bot.keyboards.truck import (
    truck_confirm_keyboard,
    truck_detail_keyboard,
    truck_priority_keyboard,
    truck_skip_keyboard,
    trucks_list_keyboard,
)


from src.bot.keyboards.qc import (
    qc_approve_confirm_keyboard,
    qc_history_detail_keyboard,
    qc_history_keyboard,
    qc_queue_keyboard,
    qc_reject_cancel_keyboard,
    qc_reject_confirm_keyboard,
    qc_review_keyboard,
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
    "invites_list_keyboard",
    "invite_role_keyboard",
    "invite_step_keyboard",
    "invite_expires_keyboard",
    "invite_max_uses_keyboard",
    "invite_confirm_keyboard",
    "invite_detail_keyboard",
    "registration_skip_phone_keyboard",
    "registration_confirm_keyboard",
    "trucks_list_keyboard",
    "truck_detail_keyboard",
    "truck_priority_keyboard",
    "truck_skip_keyboard",
    "truck_confirm_keyboard",

    # QC
    "qc_queue_keyboard",
    "qc_review_keyboard",
    "qc_approve_confirm_keyboard",
    "qc_reject_cancel_keyboard",
    "qc_reject_confirm_keyboard",
    "qc_history_keyboard",
    "qc_history_detail_keyboard",

]

from src.bot.keyboards.worker import (
    worker_history_detail_keyboard,
    worker_history_keyboard,
    worker_submit_cancel_keyboard,
    worker_submit_confirm_keyboard,
    worker_submit_skip_comment_keyboard,
    worker_task_detail_keyboard,
    worker_tasks_keyboard,
)
