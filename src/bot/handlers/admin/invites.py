"""Admin — Invite (taklif) tizimi."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsAdmin
from src.bot.keyboards.admin import admin_main_menu
from src.bot.keyboards.invite import (
    invite_cancel_keyboard,
    invite_role_keyboard,
    invite_step_keyboard,
)
from src.bot.states import CreateInviteFSM
from src.database.models.invite import Invite
from src.database.models.user import User
from src.utils.constants import (
    ROLE_NAMES,
    STEP_NAMES,
)
from src.utils.logger import logger


router = Router(name="admin_invites")


# ==== Invite yaratishni boshlash ====
@router.message(IsAdmin(), F.text == "➕ Taklif yaratish")
async def start_invite(
    message: Message,
    state: CreateInviteFSM,
):
    """Invite yaratishni boshlash."""
    await state.clear()
    await state.set_state(CreateInviteFSM.role)

    await message.answer(
        "➕ <b>Yangi taklif yaratish</b>\n\n"
        "1️⃣ <b>Rolni tanlang:</b>",
        reply_markup=invite_role_keyboard(),
    )


# ==== Rol tanlash ====
@router.callback_query(IsAdmin(), F.data.startswith("invite_role:"))
async def choose_role(
    callback: CallbackQuery,
    state: CreateInviteFSM,
):
    """Rolni tanlash."""
    role = callback.data.split(":")[1]
    await callback.answer()

    await state.update_data(role=role)

    if role == "worker":
        await state.set_state(CreateInviteFSM.step)
        await callback.message.edit_text(
            "2️⃣ <b>Ishchi bo'limini tanlang:</b>\n\n"
            "<i>Qaysi stepda ishlaydi?</i>",
            reply_markup=invite_step_keyboard(),
        )
    else:
        await state.set_state(CreateInviteFSM.confirm)
        role_name = ROLE_NAMES.get(role, role)

        await callback.message.edit_text(
            f"📋 <b>Tasdiqlash</b>\n\n"
            f"🎭 Rol: <b>{role_name}</b>\n\n"
            f"<b>Taklif yaratilsinmi?</b>",
            reply_markup=invite_cancel_keyboard(),
        )


# ==== Step tanlash ====
@router.callback_query(IsAdmin(), F.data.startswith("invite_step:"))
async def choose_step(
    callback: CallbackQuery,
    state: CreateInviteFSM,
):
    """Stepni tanlash."""
    step_number = int(callback.data.split(":")[1])
    await callback.answer()

    await state.update_data(step_number=step_number)
    await state.set_state(CreateInviteFSM.confirm)

    data = await state.get_data()
    role = data["role"]
    role_name = ROLE_NAMES.get(role, role)
    step_name = STEP_NAMES.get(step_number, f"Step {step_number}")

    await callback.message.edit_text(
        f"📋 <b>Tasdiqlash</b>\n\n"
        f"🎭 Rol: <b>{role_name}</b>\n"
        f"🔧 Bo'lim: <b>{step_name}</b>\n\n"
        f"<b>Taklif yaratilsinmi?</b>",
        reply_markup=invite_cancel_keyboard(),
    )


# ==== Invite yaratish (confirm) ====
@router.callback_query(IsAdmin(), F.data == "invite_confirm")
async def confirm_invite(
    callback: CallbackQuery,
    state: CreateInviteFSM,
    session: AsyncSession,
    user: User,
    bot: Bot,
):
    """Invite yaratishni tasdiqlash."""
    data = await state.get_data()
    role = data["role"]
    step_number = data.get("step_number")

    # Token yaratish
    token = uuid4().hex[:16]

    # Muddat: 24 soat
    expires_at = datetime.now(UTC) + timedelta(hours=24)

    invite = Invite(
        token=token,
        role=role,
        step_number=step_number,
        created_by=user.id,
        expires_at=expires_at,
    )
    session.add(invite)
    await session.flush()

    await state.clear()
    await callback.answer("✅ Taklif yaratildi")

    # Bot username
    bot_info = await bot.get_me()
    invite_link = f"https://t.me/{bot_info.username}?start={token}"

    role_name = ROLE_NAMES.get(role, role)
    step_info = ""
    if step_number:
        step_name = STEP_NAMES.get(step_number, f"Step {step_number}")
        step_info = f"\n🔧 Bo'lim: <b>{step_name}</b>"

    logger.info(
        f"➕ Invite yaratildi: role={role}, step={step_number}, "
        f"token={token}, created_by={user.id}"
    )

    await callback.message.edit_text(
        f"✅ <b>Taklif yaratildi!</b>\n\n"
        f"🎭 Rol: <b>{role_name}</b>{step_info}\n\n"
        f"🔗 <b>Havola:</b>\n"
        f"<code>{invite_link}</code>\n\n"
        f"⏰ Muddat: <b>24 soat</b>\n\n"
        f"<i>Havolani foydalanuvchiga yuboring.</i>",
        reply_markup=admin_main_menu(),
    )


# ==== Invite bekor qilish ====
@router.callback_query(IsAdmin(), F.data == "invite_cancel")
async def cancel_invite(
    callback: CallbackQuery,
    state: CreateInviteFSM,
):
    """Invite yaratishni bekor qilish."""
    await callback.answer("❌ Bekor qilindi")
    await state.clear()

    await callback.message.edit_text(
        "❌ <b>Bekor qilindi.</b>\n\n"
        "Admin panelga qaytish uchun /start bosing.",
        reply_markup=admin_main_menu(),
    )
