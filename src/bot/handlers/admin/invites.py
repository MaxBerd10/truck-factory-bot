"""Admin — Invite (taklif) tizimi."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsAdmin
from src.bot.keyboards.admin import (
    invite_cancel_keyboard,
    invite_role_keyboard,
    invite_step_keyboard,
)
from src.bot.keyboards.reply import admin_menu_keyboard
from src.bot.states import CreateInviteFSM
from src.database.models.invite import Invite
from src.database.models.user import User
from src.services.i18n_service import _, get_role_name, get_step_name
from src.utils.logger import logger


router = Router(name="admin_invites")


# ==================== Invite yaratishni boshlash ====================
@router.message(IsAdmin(), F.text == "➕ Taklif yaratish")
async def start_invite(
    message: Message,
    state: FSMContext,
    user: User,
):
    """Invite yaratishni boshlash."""
    lang = user.language or "uz"
    await state.clear()
    await state.set_state(CreateInviteFSM.role)

    await message.answer(
        _("admin.invite_step1", language=lang),
        reply_markup=invite_role_keyboard(lang),
    )


# ==================== Rol tanlash ====================
@router.callback_query(
    CreateInviteFSM.role,
    F.data.startswith("invite_role:"),
)
async def choose_role(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Rolni tanlash."""
    lang = user.language or "uz"
    role = callback.data.split(":")[1]
    await callback.answer()

    await state.update_data(role=role)

    if role == "worker":
        await state.set_state(CreateInviteFSM.step_number)
        await callback.message.edit_text(
            _("admin.invite_step2_worker", language=lang),
            reply_markup=invite_step_keyboard(lang),
        )
    else:
        await state.set_state(CreateInviteFSM.confirm)
        role_name = get_role_name(role, lang)

        await callback.message.edit_text(
            _(
                "admin.invite_confirm",
                language=lang,
                role=role_name,
                step="—",
            ),
            reply_markup=invite_cancel_keyboard(lang),
        )


# ==================== Step tanlash ====================
@router.callback_query(
    CreateInviteFSM.step_number,
    F.data.startswith("invite_step:"),
)
async def choose_step(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Stepni tanlash."""
    lang = user.language or "uz"
    step_number = int(callback.data.split(":")[1])
    await callback.answer()

    await state.update_data(step_number=step_number)
    await state.set_state(CreateInviteFSM.confirm)

    data = await state.get_data()
    role_name = get_role_name(data["role"], lang)
    step_name = get_step_name(step_number, lang)

    await callback.message.edit_text(
        _(
            "admin.invite_confirm",
            language=lang,
            role=role_name,
            step=step_name,
        ),
        reply_markup=invite_cancel_keyboard(lang),
    )


# ==================== Invite yaratish ====================
@router.callback_query(
    CreateInviteFSM.confirm,
    F.data == "invite_confirm",
)
async def confirm_invite(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User,
    bot: Bot,
):
    """Invite yaratishni tasdiqlash."""
    lang = user.language or "uz"
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
        created_by=user.telegram_id,
        expires_at=expires_at,
    )
    session.add(invite)
    await session.flush()

    await state.clear()
    await callback.answer(_("admin.invite_created", language=lang))

    # Bot username
    bot_info = await bot.get_me()
    invite_link = f"https://t.me/{bot_info.username}?start={token}"

    role_name = get_role_name(role, lang)
    step_info = ""
    if step_number:
        step_name = get_step_name(step_number, lang)
        step_info = f"\n🔧 {step_name}"

    logger.info(
        f"➕ Invite yaratildi: role={role}, step={step_number}, "
        f"token={token}, created_by={user.telegram_id}"
    )

    await callback.message.edit_text(
        f"✅ <b>{_('admin.invite_created', language=lang)}</b>\n\n"
        f"🎭 {role_name}{step_info}\n\n"
        f"🔗 <b>Havola:</b>\n"
        f"<code>{invite_link}</code>\n\n"
        f"⏰ {_('admin.invite_expires', language=lang)}\n\n"
        f"<i>{_('admin.invite_hint', language=lang)}</i>",
        reply_markup=admin_menu_keyboard(lang),
    )


# ==================== Bekor qilish ====================
@router.callback_query(F.data == "invite_cancel")
async def cancel_invite(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Invite yaratishni bekor qilish."""
    lang = user.language or "uz"
    await callback.answer(_("common.cancel", language=lang))
    await state.clear()

    await callback.message.edit_text(
        _("common.cancelled", language=lang),
    )
