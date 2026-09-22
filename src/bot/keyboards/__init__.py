"""Keyboards."""
from src.bot.keyboards.admin import (
    admin_main_menu,
    cancel_add_user_keyboard,
    confirm_add_user_keyboard,
    export_keyboard,
    role_choice_keyboard,
    skip_phone_keyboard,
    step_choice_keyboard,
    user_detail_keyboard,
    users_list_keyboard,
)
from src.bot.keyboards.invite import (
    invite_cancel_keyboard,
    invite_role_keyboard,
    invite_step_keyboard,
)
from src.bot.keyboards.qc import (
    qc_after_action_keyboard,
    qc_approve_confirm_keyboard,
    qc_history_detail_keyboard,
    qc_history_keyboard,
    qc_queue_keyboard,
    qc_reject_cancel_keyboard,
    qc_reject_confirm_keyboard,
    qc_review_keyboard,
)
from src.bot.keyboards.registration import (
    registration_cancel_keyboard,
    registration_confirm_keyboard,
    registration_skip_phone_keyboard,
)
from src.bot.keyboards.reply import (
    admin_menu_keyboard,
    qc_menu_keyboard,
    worker_menu_keyboard,
)
from src.bot.keyboards.truck import (
    truck_confirm_keyboard,
    truck_detail_keyboard,
    truck_priority_keyboard,
    truck_skip_keyboard,
    trucks_list_keyboard,
)
from src.bot.keyboards.worker import (
    worker_after_submit_keyboard,
    worker_history_detail_keyboard,
    worker_history_keyboard,
    worker_submit_cancel_keyboard,
    worker_submit_confirm_keyboard,
    worker_submit_skip_comment_keyboard,
    worker_task_detail_keyboard,
    worker_tasks_keyboard,
)


def main_menu_keyboard(role: str):
    """Rolga qarab asosiy menyu keyboard ini qaytarish."""
    if role == "admin":
        return admin_menu_keyboard()
    if role == "qc":
        return qc_menu_keyboard()
    return worker_menu_keyboard()


__all__ = [
    # Admin
    "admin_main_menu",
    "cancel_add_user_keyboard",
    "confirm_add_user_keyboard",
    "role_choice_keyboard",
    "skip_phone_keyboard",
    "step_choice_keyboard",
    "user_detail_keyboard",
    "users_list_keyboard",
    # Invite
    "invite_cancel_keyboard",
    "invite_role_keyboard",
    "invite_step_keyboard",
    # QC
    "qc_after_action_keyboard",
    "qc_approve_confirm_keyboard",
    "qc_history_detail_keyboard",
    "qc_history_keyboard",
    "qc_queue_keyboard",
    "qc_reject_cancel_keyboard",
    "qc_reject_confirm_keyboard",
    "qc_review_keyboard",
    # Registration
    "registration_cancel_keyboard",
    "registration_confirm_keyboard",
    "registration_skip_phone_keyboard",
    # Reply
    "admin_menu_keyboard",
    "qc_menu_keyboard",
    "worker_menu_keyboard",
    "main_menu_keyboard",
    # Truck
    "truck_confirm_keyboard",
    "truck_detail_keyboard",
    "truck_priority_keyboard",
    "truck_skip_keyboard",
    "trucks_list_keyboard",
    # Worker
    "worker_after_submit_keyboard",
    "worker_history_detail_keyboard",
    "worker_history_keyboard",
    "worker_submit_cancel_keyboard",
    "worker_submit_confirm_keyboard",
    "worker_submit_skip_comment_keyboard",
    "worker_task_detail_keyboard",
    "worker_tasks_keyboard",

    "export_keyboard",
]
