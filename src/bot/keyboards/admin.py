"""Admin keyboard lar (i18n bilan)."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database.models.user import User
from src.services.i18n_service import _, get_step_name


# ==================== ASOSIY MENYU ====================

def admin_main_menu(language: str = "uz") -> InlineKeyboardMarkup:
    """Admin asosiy menyu (inline)."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_("admin.menu_trucks", language=language),
        callback_data="admin_trucks",
    )
    builder.button(
        text=_("admin.menu_users", language=language),
        callback_data="admin_users",
    )
    builder.button(
        text=_("admin.menu_new_truck", language=language),
        callback_data="admin_truck_add",
    )
    builder.button(
        text=_("admin.menu_stats", language=language),
        callback_data="admin_stats",
    )
    builder.adjust(2)
    return builder.as_markup()


# ==================== USERS ====================

def users_list_keyboard(
    users: list[User],
    page: int = 0,
    per_page: int = 10,
    total: int = 0,
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Foydalanuvchilar ro'yxati keyboard i."""
    builder = InlineKeyboardBuilder()

    for u in users:
        role_icon = {
            "admin": "👑",
            "qc": "🔍",
            "worker": "👷",
        }.get(u.role, "👤")

        status_icon = "✅" if u.is_active else "🚫"

        step_info = ""
        if u.step_number:
            step_name = get_step_name(u.step_number, language)
            step_info = f" — {step_name}"

        builder.button(
            text=f"{status_icon} {role_icon} {u.full_name}{step_info}",
            callback_data=f"user_view:{u.id}",
        )

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text=f"⬅️ {_('common.back', language=language)}",
                callback_data=f"users_page:{page - 1}",
            )
        )

    total_pages = (total + per_page - 1) // per_page if per_page else 1
    if total_pages > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data="noop",
            )
        )

    if (page + 1) * per_page < total:
        nav_buttons.append(
            InlineKeyboardButton(
                text=f"{_('common.retry', language=language)} ➡️",
                callback_data=f"users_page:{page + 1}",
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(
            text=f"➕ {_('admin.user_add_title', language=language)}",
            callback_data="user_add",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=f"🔙 {_('common.main_menu', language=language)}",
            callback_data="main_menu",
        )
    )

    return builder.as_markup()


def user_detail_keyboard(
    user: User,
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Bitta user tafsiloti keyboard i."""
    builder = InlineKeyboardBuilder()

    if user.is_active:
        builder.button(
            text=f"🚫 {_('admin.user_block', language=language)}",
            callback_data=f"user_block:{user.id}",
        )
    else:
        builder.button(
            text=f"✅ {_('admin.user_unblock', language=language)}",
            callback_data=f"user_unblock:{user.id}",
        )

    builder.button(
        text=f"🔙 {_('common.back', language=language)}",
        callback_data="users_page:0",
    )
    builder.button(
        text=f"🏠 {_('common.main_menu', language=language)}",
        callback_data="main_menu",
    )
    builder.adjust(1, 2)

    return builder.as_markup()


# ==================== USER ADD (FSM) ====================

def cancel_add_user_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    """Foydalanuvchi qo'shishni bekor qilish."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="user_add_cancel",
    )
    return builder.as_markup()


def role_choice_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    """Rol tanlash (user add uchun)."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"👷 {_('roles.worker', language=language)}",
        callback_data="add_user_role:worker",
    )
    builder.button(
        text=f"🔍 {_('roles.qc', language=language)}",
        callback_data="add_user_role:qc",
    )
    builder.button(
        text=f"👑 {_('roles.admin', language=language)}",
        callback_data="add_user_role:admin",
    )
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="user_add_cancel",
    )
    builder.adjust(1)
    return builder.as_markup()


def step_choice_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    """Step tanlash (ishchi uchun)."""
    builder = InlineKeyboardBuilder()
    for step_num in range(1, 7):
        step_name = get_step_name(step_num, language)
        builder.button(
            text=f"{step_num}️⃣ {step_name}",
            callback_data=f"add_user_step:{step_num}",
        )
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="user_add_cancel",
    )
    builder.adjust(1)
    return builder.as_markup()


def skip_phone_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    """Telefon raqamini o'tkazib yuborish."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"⏭ {_('common.skip', language=language)}",
        callback_data="user_add_skip_phone",
    )
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="user_add_cancel",
    )
    builder.adjust(2)
    return builder.as_markup()


def confirm_add_user_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    """User qo'shishni tasdiqlash."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"✅ {_('common.confirm', language=language)}",
        callback_data="user_add_confirm",
    )
    builder.button(
        text=f"✏️ {_('common.retry', language=language)}",
        callback_data="user_add_restart",
    )
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="user_add_cancel",
    )
    builder.adjust(2, 1)
    return builder.as_markup()


# ==================== TRUCK ====================

def truck_confirm_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    """Truck yaratishni tasdiqlash."""
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


def truck_cancel_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    """Truck yaratishni bekor qilish."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="truck_cancel",
    )
    return builder.as_markup()


def truck_priority_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    """Prioritet tanlash."""
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


def trucks_list_keyboard(
    trucks: list,
    page: int = 0,
    per_page: int = 5,
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Trucklar ro'yxati."""
    builder = InlineKeyboardBuilder()

    for truck in trucks:
        status_icon = {
            "in_progress": "🔵",
            "completed": "✅",
            "cancelled": "❌",
        }.get(truck.status, "⚪")

        builder.button(
            text=f"{status_icon} {truck.serial_number} — {truck.current_step}/6",
            callback_data=f"truck_view:{truck.id}",
        )

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text=f"⬅️ {_('common.back', language=language)}",
                callback_data=f"trucks_page:{page - 1}",
            )
        )
    nav_buttons.append(
        InlineKeyboardButton(
            text=f"➕ {_('admin.menu_new_truck', language=language)}",
            callback_data="truck_add",
        )
    )
    if len(trucks) == per_page:
        nav_buttons.append(
            InlineKeyboardButton(
                text=f"{_('common.retry', language=language)} ➡️",
                callback_data=f"trucks_page:{page + 1}",
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(
            text=f"🔙 {_('common.main_menu', language=language)}",
            callback_data="main_menu",
        )
    )

    return builder.as_markup()


def truck_detail_keyboard(
    truck,
    back_page: int = 0,
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Truck tafsiloti keyboard i."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=f"📅 {_('admin.timeline_title', language=language)}",
        callback_data=f"truck_timeline:{truck.id}",
    )

    if truck.status == "in_progress":
        builder.button(
            text=f"❌ {_('common.cancel', language=language)}",
            callback_data=f"truck_cancel_confirm:{truck.id}",
        )

    builder.button(
        text=f"🔙 {_('common.back', language=language)}",
        callback_data=f"trucks_page:{back_page}",
    )
    builder.button(
        text=f"🏠 {_('common.main_menu', language=language)}",
        callback_data="main_menu",
    )
    builder.adjust(1, 1, 2)

    return builder.as_markup()


def truck_steps_keyboard(
    truck,
    steps: list,
    language: str = "uz",
) -> InlineKeyboardMarkup:
    """Truck steplari keyboard i."""
    builder = InlineKeyboardBuilder()

    for step in steps:
        status_icon = {
            "pending": "⏳",
            "in_review": "🔍",
            "approved": "✅",
            "rejected": "❌",
        }.get(step.status, "⚪")

        step_name = get_step_name(step.step_number, language)

        builder.button(
            text=f"{status_icon} {step.step_number}. {step_name}",
            callback_data=f"truck_step_view:{step.id}",
        )

    builder.button(
        text=f"🔙 {_('common.back', language=language)}",
        callback_data=f"truck_view:{truck.id}",
    )
    builder.adjust(1)

    return builder.as_markup()


# ==================== EXPORT ====================

def export_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    """Excel hisobot uchun keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_("admin.excel_trucks_all", language=language),
        callback_data="export_trucks_all",
    )
    builder.button(
        text=_("admin.excel_trucks_completed", language=language),
        callback_data="export_trucks_completed",
    )
    builder.button(
        text=_("admin.excel_trucks_in_progress", language=language),
        callback_data="export_trucks_in_progress",
    )
    builder.button(
        text=_("admin.excel_steps_all", language=language),
        callback_data="export_steps_all",
    )
    builder.button(
        text=f"🔙 {_('common.main_menu', language=language)}",
        callback_data="main_menu",
    )
    builder.adjust(1)
    return builder.as_markup()


# ==================== INVITE ====================

def invite_role_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    """Invite rol tanlash."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"👷 {_('roles.worker', language=language)}",
        callback_data="invite_role:worker",
    )
    builder.button(
        text=f"🔍 {_('roles.qc', language=language)}",
        callback_data="invite_role:qc",
    )
    builder.button(
        text=f"👑 {_('roles.admin', language=language)}",
        callback_data="invite_role:admin",
    )
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="invite_cancel",
    )
    builder.adjust(1)
    return builder.as_markup()


def invite_step_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    """Invite step tanlash."""
    builder = InlineKeyboardBuilder()
    for step_num in range(1, 7):
        step_name = get_step_name(step_num, language)
        builder.button(
            text=f"{step_num}️⃣ {step_name}",
            callback_data=f"invite_step:{step_num}",
        )
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="invite_cancel",
    )
    builder.adjust(1)
    return builder.as_markup()


def invite_cancel_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    """Invite tasdiqlash."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"✅ {_('common.confirm', language=language)}",
        callback_data="invite_confirm",
    )
    builder.button(
        text=f"❌ {_('common.cancel', language=language)}",
        callback_data="invite_cancel",
    )
    builder.adjust(2)
    return builder.as_markup()
