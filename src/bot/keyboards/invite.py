"""Invite linklar uchun keyboard lar."""
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database.models.invite import Invite
from src.utils.constants import ROLE_NAMES, STEP_NAMES


def invites_list_keyboard(invites: list[Invite], bot_username: str):
    """Invite lar ro'yxati uchun keyboard."""
    builder = InlineKeyboardBuilder()

    for invite in invites:
        role_name = ROLE_NAMES.get(invite.role, invite.role)
        step_text = ""
        if invite.step_number:
            step_text = f" — {STEP_NAMES.get(invite.step_number, invite.step_number)}"

        builder.button(
            text=f"🔗 {role_name}{step_text}",
            callback_data=f"invite_view:{invite.id}",
        )

    builder.adjust(1)

    builder.row(
        InlineKeyboardButton(text="➕ Yangi yaratish", callback_data="invite_add"),
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="invites_refresh"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu"),
    )

    return builder.as_markup()


def invite_role_keyboard():
    """Invite uchun rol tanlash."""
    builder = InlineKeyboardBuilder()
    builder.button(text="👷 Ishchi", callback_data="invite_role:worker")
    builder.button(text="🔍 Sifat nazoratchisi", callback_data="invite_role:qc")
    builder.button(text="👑 Administrator", callback_data="invite_role:admin")
    builder.button(text="❌ Bekor qilish", callback_data="invite_cancel")
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()


def invite_step_keyboard():
    """Invite uchun step tanlash."""
    builder = InlineKeyboardBuilder()
    for step_num, step_name in STEP_NAMES.items():
        builder.button(
            text=step_name,
            callback_data=f"invite_step:{step_num}",
        )
    builder.button(text="❌ Bekor qilish", callback_data="invite_cancel")
    builder.adjust(1, 1, 1, 1, 1, 1, 1)
    return builder.as_markup()


def invite_expires_keyboard():
    """Invite uchun muddat tanlash."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🕐 1 soat", callback_data="invite_expires:1")
    builder.button(text="📅 1 kun", callback_data="invite_expires:24")
    builder.button(text="📅 7 kun", callback_data="invite_expires:168")
    builder.button(text="📅 30 kun", callback_data="invite_expires:720")
    builder.button(text="♾ Cheksiz", callback_data="invite_expires:none")
    builder.button(text="❌ Bekor qilish", callback_data="invite_cancel")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def invite_max_uses_keyboard():
    """Invite uchun ishlatish soni."""
    builder = InlineKeyboardBuilder()
    builder.button(text="1️⃣ Bir martalik", callback_data="invite_max_uses:1")
    builder.button(text="5️⃣ 5 marta", callback_data="invite_max_uses:5")
    builder.button(text="🔟 10 marta", callback_data="invite_max_uses:10")
    builder.button(text="♾ Cheksiz", callback_data="invite_max_uses:0")
    builder.button(text="❌ Bekor qilish", callback_data="invite_cancel")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def invite_confirm_keyboard():
    """Tasdiqlash."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yaratish", callback_data="invite_confirm")
    builder.button(text="✏️ Qaytadan", callback_data="invite_restart")
    builder.button(text="❌ Bekor qilish", callback_data="invite_cancel")
    builder.adjust(2, 1)
    return builder.as_markup()


def invite_detail_keyboard(invite: Invite, bot_username: str):
    """Bitta invite tafsilotlari uchun keyboard."""
    builder = InlineKeyboardBuilder()

    link = f"https://t.me/{bot_username}?start={invite.code}"
    builder.button(
        text="📤 Ulashish",
        url=f"https://t.me/share/url?url={link}&text=Taklif%20havolasi",
    )

    builder.button(
        text="🗑 O'chirish",
        callback_data=f"invite_delete:{invite.id}",
    )

    builder.button(text="🔙 Ro'yxatga", callback_data="invites_refresh")

    builder.adjust(1, 1, 1)
    return builder.as_markup()
