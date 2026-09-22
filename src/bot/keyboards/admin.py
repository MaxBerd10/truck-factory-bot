"""Admin uchun inline keyboard lar."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database.models.user import User
from src.utils.constants import ROLE_NAMES, STEP_NAMES, STEP_SHORT_NAMES

# ==== Foydalanuvchilar ro'yxati ====
def users_list_keyboard(
    users: list[User],
    page: int = 0,
    per_page: int = 10,
    total: int = 0,
) -> InlineKeyboardMarkup:
    """Foydalanuvchilar ro'yxati uchun keyboard (sahifalab).

    Args:
        users: Bu sahifadagi userlar
        page: Hozirgi sahifa (0 dan boshlanadi)
        per_page: Bir sahifada nechta
        total: Jami userlar soni
    """
    builder = InlineKeyboardBuilder()

    # Har bir user uchun tugma
    for user in users:
        role_icon = {
            "worker": "👷",
            "qc": "🔍",
            "admin": "👑",
        }.get(user.role, "❓")

        # Step yoki rol nomi
        if user.is_worker and user.step_number:
            step_name = STEP_SHORT_NAMES.get(user.step_number, f"Step {user.step_number}")
            subtitle = f"{step_name}"
        else:
            subtitle = ROLE_NAMES.get(user.role, user.role).split(" ", 1)[-1]

        # Active emoji
        active = "" if user.is_active else "🚫 "

        builder.button(
            text=f"{active}{role_icon} {user.full_name} — {subtitle}",
            callback_data=f"user_view:{user.id}",
        )

    # Har bir tugma alohida qatorda
    builder.adjust(1)

    # ==== Navigatsiya ====
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"users_page:{page - 1}")
        )
    if total > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text=f"📄 {page + 1}/{total_pages}",
                callback_data="noop",
            )
        )
    if (page + 1) * per_page < total:
        nav_buttons.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"users_page:{page + 1}")
        )

    # Amallar
    builder.row(
        InlineKeyboardButton(text="➕ Yangi qo'shish", callback_data="user_add"),
        InlineKeyboardButton(text="🔄 Yangilash", callback_data=f"users_page:{page}"),
    )

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu"),
    )

    return builder.as_markup()


# ==== Bitta user uchun ====
def user_detail_keyboard(user: User, back_page: int = 0) -> InlineKeyboardMarkup:
    """Bitta foydalanuvchi tafsilotlari uchun keyboard."""
    builder = InlineKeyboardBuilder()

    # Bloklash / Aktivlashtirish
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

    # Tahrirlash
    builder.button(
        text="✏️ Tahrirlash",
        callback_data=f"user_edit:{user.id}",
    )

    # Orqaga
    builder.button(
        text="🔙 Ro'yxatga",
        callback_data=f"users_page:{back_page}",
    )

    builder.adjust(1, 1, 1)
    return builder.as_markup()


# ==== Yangi user qo'shish uchun keyboard lar ====

def skip_phone_keyboard() -> InlineKeyboardMarkup:
    """Telefon raqamni o'tkazib yuborish."""
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ O'tkazib yuborish", callback_data="add_user_skip_phone")
    builder.button(text="❌ Bekor qilish", callback_data="add_user_cancel")
    builder.adjust(2)
    return builder.as_markup()


def cancel_add_user_keyboard() -> InlineKeyboardMarkup:
    """Bekor qilish."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="add_user_cancel")
    return builder.as_markup()


def role_choice_keyboard() -> InlineKeyboardMarkup:
    """Rol tanlash."""
    builder = InlineKeyboardBuilder()
    builder.button(text="👷 Ishchi", callback_data="add_user_role:worker")
    builder.button(text="🔍 Sifat nazoratchisi", callback_data="add_user_role:qc")
    builder.button(text="👑 Administrator", callback_data="add_user_role:admin")
    builder.button(text="❌ Bekor qilish", callback_data="add_user_cancel")
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()


def step_choice_keyboard() -> InlineKeyboardMarkup:
    """Step tanlash (worker uchun)."""
    builder = InlineKeyboardBuilder()

    for step_num, step_name in STEP_NAMES.items():
        builder.button(
            text=step_name,
            callback_data=f"add_user_step:{step_num}",
        )

    builder.button(text="❌ Bekor qilish", callback_data="add_user_cancel")
    builder.adjust(1, 1, 1, 1, 1, 1, 1)
    return builder.as_markup()


def confirm_add_user_keyboard() -> InlineKeyboardMarkup:
    """Tasdiqlash."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Saqlash", callback_data="add_user_confirm")
    builder.button(text="✏️ Qaytadan", callback_data="add_user_restart")
    builder.button(text="❌ Bekor qilish", callback_data="add_user_cancel")
    builder.adjust(2, 1)
    return builder.as_markup()
