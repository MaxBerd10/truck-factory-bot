"""Admin keyboard lar."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database.models.user import User
from src.utils.constants import ROLE_NAMES, STEP_NAMES


# ==================== ASOSIY MENYU ====================

def admin_main_menu() -> InlineKeyboardMarkup:
    """Admin asosiy menyu (inline)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🚛 Trucklar", callback_data="admin_trucks")
    builder.button(text="👥 Foydalanuvchilar", callback_data="admin_users")
    builder.button(text="➕ Yangi truck", callback_data="admin_truck_add")
    builder.button(text="📊 Statistika", callback_data="admin_stats")
    builder.adjust(2)
    return builder.as_markup()


# ==================== USERS ====================

def users_list_keyboard(
    users: list[User],
    page: int = 0,
    per_page: int = 10,
    total: int = 0,
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
            step_info = f" — {STEP_NAMES.get(u.step_number, u.step_number)}"

        builder.button(
            text=f"{status_icon} {role_icon} {u.full_name}{step_info}",
            callback_data=f"user_view:{u.id}",
        )

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Oldingi",
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
                text="Keyingi ➡️",
                callback_data=f"users_page:{page + 1}",
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(
            text="➕ Yangi foydalanuvchi",
            callback_data="user_add",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="🔙 Asosiy menyu",
            callback_data="main_menu",
        )
    )

    return builder.as_markup()


def user_detail_keyboard(user: User) -> InlineKeyboardMarkup:
    """Bitta user tafsiloti keyboard i."""
    builder = InlineKeyboardBuilder()

    if user.is_active:
        builder.button(
            text="🚫 Bloklash",
            callback_data=f"user_block:{user.id}",
        )
    else:
        builder.button(
            text="✅ Aktivlashtirish",
            callback_data=f"user_unblock:{user.id}",
        )

    builder.button(
        text="🔙 Ro'yxatga",
        callback_data="users_page:0",
    )
    builder.button(
        text="🏠 Asosiy menyu",
        callback_data="main_menu",
    )
    builder.adjust(1, 2)

    return builder.as_markup()


# ==================== USER ADD (FSM) ====================

def cancel_add_user_keyboard() -> InlineKeyboardMarkup:
    """Foydalanuvchi qo'shishni bekor qilish (har bir qadamda)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="user_add_cancel")
    return builder.as_markup()


def role_choice_keyboard() -> InlineKeyboardMarkup:
    """Rol tanlash (user add uchun)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="👷 Ishchi", callback_data="add_user_role:worker")
    builder.button(text="🔍 Sifat nazoratchisi", callback_data="add_user_role:qc")
    builder.button(text="👑 Administrator", callback_data="add_user_role:admin")
    builder.button(text="❌ Bekor qilish", callback_data="user_add_cancel")
    builder.adjust(1)
    return builder.as_markup()


def step_choice_keyboard() -> InlineKeyboardMarkup:
    """Step tanlash (ishchi uchun)."""
    builder = InlineKeyboardBuilder()
    for step_num in range(1, 7):
        step_name = STEP_NAMES.get(step_num, f"Step {step_num}")
        builder.button(
            text=f"{step_num}️⃣ {step_name}",
            callback_data=f"add_user_step:{step_num}",
        )
    builder.button(text="❌ Bekor qilish", callback_data="user_add_cancel")
    builder.adjust(1)
    return builder.as_markup()


def skip_phone_keyboard() -> InlineKeyboardMarkup:
    """Telefon raqamini o'tkazib yuborish."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⏭ O'tkazib yuborish",
        callback_data="user_add_skip_phone",
    )
    builder.button(text="❌ Bekor qilish", callback_data="user_add_cancel")
    builder.adjust(2)
    return builder.as_markup()


def confirm_add_user_keyboard() -> InlineKeyboardMarkup:
    """User qo'shishni tasdiqlash."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yaratish", callback_data="user_add_confirm")
    builder.button(text="✏️ Qaytadan", callback_data="user_add_restart")
    builder.button(text="❌ Bekor qilish", callback_data="user_add_cancel")
    builder.adjust(2, 1)
    return builder.as_markup()


# ==================== TRUCK ====================

def truck_confirm_keyboard() -> InlineKeyboardMarkup:
    """Truck yaratishni tasdiqlash."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yaratish", callback_data="truck_confirm")
    builder.button(text="✏️ Qaytadan", callback_data="truck_restart")
    builder.button(text="❌ Bekor qilish", callback_data="truck_cancel")
    builder.adjust(2, 1)
    return builder.as_markup()


def truck_priority_keyboard() -> InlineKeyboardMarkup:
    """Prioritet tanlash."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🟢 Past", callback_data="truck_priority:low")
    builder.button(text="🔵 Oddiy", callback_data="truck_priority:normal")
    builder.button(text="🟠 Yuqori", callback_data="truck_priority:high")
    builder.button(text="🔴 Shoshilinch", callback_data="truck_priority:urgent")
    builder.button(text="❌ Bekor qilish", callback_data="truck_cancel")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def truck_cancel_keyboard() -> InlineKeyboardMarkup:
    """Truck yaratishni bekor qilish."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="truck_cancel")
    return builder.as_markup()


def trucks_list_keyboard(
    trucks: list,
    page: int = 0,
    per_page: int = 5,
) -> InlineKeyboardMarkup:
    """Trucklar ro'yxati (admin.py ichida, kerak bo'lsa)."""
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
                text="⬅️ Oldingi",
                callback_data=f"trucks_page:{page - 1}",
            )
        )
    nav_buttons.append(
        InlineKeyboardButton(
            text="➕ Yangi truck",
            callback_data="truck_add",
        )
    )
    if len(trucks) == per_page:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Keyingi ➡️",
                callback_data=f"trucks_page:{page + 1}",
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(
            text="🔙 Asosiy menyu",
            callback_data="main_menu",
        )
    )

    return builder.as_markup()


def truck_detail_keyboard(truck) -> InlineKeyboardMarkup:
    """Truck tafsiloti keyboard i."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text="📋 Steplarni ko'rish",
        callback_data=f"truck_steps:{truck.id}",
    )

    if truck.status == "in_progress":
        builder.button(
            text="❌ Bekor qilish",
            callback_data=f"truck_cancel_confirm:{truck.id}",
        )

    builder.button(
        text="🔙 Trucklar ro'yxati",
        callback_data="trucks_page:0",
    )
    builder.button(
        text="🏠 Asosiy menyu",
        callback_data="main_menu",
    )
    builder.adjust(1, 1, 2)

    return builder.as_markup()


def truck_steps_keyboard(truck, steps: list) -> InlineKeyboardMarkup:
    """Truck steplari keyboard i."""
    builder = InlineKeyboardBuilder()

    for step in steps:
        status_icon = {
            "pending": "⏳",
            "in_review": "🔍",
            "approved": "✅",
            "rejected": "❌",
        }.get(step.status, "⚪")

        step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")

        builder.button(
            text=f"{status_icon} {step.step_number}. {step_name}",
            callback_data=f"truck_step_view:{step.id}",
        )

    builder.button(
        text="🔙 Truckga qaytish",
        callback_data=f"truck_view:{truck.id}",
    )
    builder.adjust(1)

    return builder.as_markup()
