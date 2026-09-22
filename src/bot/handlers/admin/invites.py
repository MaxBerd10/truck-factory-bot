"""Admin — Invite linklar boshqaruvi."""
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsAdmin
from src.bot.keyboards.invite import (
    invite_confirm_keyboard,
    invite_detail_keyboard,
    invite_expires_keyboard,
    invite_max_uses_keyboard,
    invite_role_keyboard,
    invite_step_keyboard,
    invites_list_keyboard,
)
from src.bot.keyboards.reply import admin_main_menu
from src.bot.states import CreateInviteFSM
from src.config import settings
from src.database.models.invite import Invite
from src.database.models.user import User
from src.services.invite_service import (
    create_invite,
    delete_invite,
    get_active_invites,
)
from src.utils.constants import ROLE_NAMES, STEP_NAMES
from src.utils.logger import logger


router = Router(name="admin_invites")


# ==== Invite linklar bo'limi ====
@router.message(IsAdmin(), F.text == "🔗 Invite linklar")
async def show_invites_menu(
    message: Message,
    session: AsyncSession,
):
    """Invite linklar ro'yxatini ko'rsatish."""
    invites = await get_active_invites(session)
    bot_username = settings.BOT_USERNAME

    if not invites:
        text = (
            "🔗 <b>Invite linklar</b>\n\n"
            "Hozircha faol havolalar yo'q.\n\n"
            "➕ Yangi havola yaratish uchun quyidagi tugmani bosing."
        )
    else:
        text = (
            f"🔗 <b>Invite linklar</b>\n\n"
            f"Faol havolalar: <b>{len(invites)}</b> ta\n\n"
            f"Batafsil ko'rish uchun havolani tanlang:"
        )

    await message.answer(
        text,
        reply_markup=invites_list_keyboard(invites, bot_username),
    )


# ==== Yangilash ====
@router.callback_query(IsAdmin(), F.data == "invites_refresh")
async def refresh_invites(
    callback: CallbackQuery,
    session: AsyncSession,
):
    """Invite ro'yxatini yangilash."""
    await callback.answer()

    invites = await get_active_invites(session)
    bot_username = settings.BOT_USERNAME

    if not invites:
        text = (
            "🔗 <b>Invite linklar</b>\n\n"
            "Hozircha faol havolalar yo'q."
        )
    else:
        text = (
            f"🔗 <b>Invite linklar</b>\n\n"
            f"Faol havolalar: <b>{len(invites)}</b> ta\n\n"
            f"Batafsil ko'rish uchun havolani tanlang:"
        )

    await callback.message.edit_text(
        text,
        reply_markup=invites_list_keyboard(invites, bot_username),
    )


# ==== Havolani ko'rish ====
@router.callback_query(IsAdmin(), F.data.startswith("invite_view:"))
async def view_invite(
    callback: CallbackQuery,
    session: AsyncSession,
):
    """Bitta invite ni ko'rish."""
    invite_id = int(callback.data.split(":")[1])

    invite = await session.get(Invite, invite_id)
    if not invite:
        await callback.answer("❌ Havola topilmadi", show_alert=True)
        return

    await callback.answer()

    role_name = ROLE_NAMES.get(invite.role, invite.role)
    step_text = "—"
    if invite.step_number:
        step_text = STEP_NAMES.get(invite.step_number, str(invite.step_number))

    # Muddat
    if invite.expires_at:
        expires_text = invite.expires_at.strftime("%Y-%m-%d %H:%M UTC")
    else:
        expires_text = "♾ Cheksiz"

    # Holat
    if invite.is_used:
        status = "✅ Ishlatilgan"
    elif invite.is_expired:
        status = "⏰ Muddati o'tgan"
    else:
        status = "🟢 Faol"

    # Havola
    link = f"https://t.me/{settings.BOT_USERNAME}?start={invite.code}"

    text = (
        f"🔗 <b>Invite ma'lumotlari</b>\n\n"
        f"📝 Kod: <code>{invite.code}</code>\n"
        f"🎭 Rol: {role_name}\n"
        f"🔧 Bo'lim: {step_text}\n"
        f"⏰ Muddat: {expires_text}\n"
        f"📊 Holat: {status}\n"
        f"📅 Yaratilgan: {invite.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"<b>Havola:</b>\n"
        f"<code>{link}</code>\n\n"
        f"<i>Havolani nusxalash uchun bosing yoki uzoq bosing.</i>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=invite_detail_keyboard(invite, settings.BOT_USERNAME),
    )


# ==== O'chirish ====
@router.callback_query(IsAdmin(), F.data.startswith("invite_delete:"))
async def confirm_delete_invite(
    callback: CallbackQuery,
    session: AsyncSession,
):
    """Havolani o'chirishni tasdiqlash."""
    invite_id = int(callback.data.split(":")[1])

    invite = await session.get(Invite, invite_id)
    if not invite:
        await callback.answer("❌ Havola topilmadi", show_alert=True)
        return

    await delete_invite(session, invite)
    await callback.answer("🗑 Havola o'chirildi", show_alert=True)

    # Ro'yxatga qaytish
    invites = await get_active_invites(session)

    if not invites:
        text = (
            "🔗 <b>Invite linklar</b>\n\n"
            "Hozircha faol havolalar yo'q."
        )
    else:
        text = (
            f"🔗 <b>Invite linklar</b>\n\n"
            f"Faol havolalar: <b>{len(invites)}</b> ta"
        )

    await callback.message.edit_text(
        text,
        reply_markup=invites_list_keyboard(invites, settings.BOT_USERNAME),
    )


# ==== Yangi invite yaratish (FSM) ====
@router.callback_query(IsAdmin(), F.data == "invite_add")
async def start_add_invite(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Yangi invite yaratishni boshlash."""
    await callback.answer()
    await state.clear()
    await state.set_state(CreateInviteFSM.role)

    await callback.message.edit_text(
        "➕ <b>Yangi invite link yaratish</b>\n\n"
        "1️⃣ <b>Rolni tanlang:</b>",
        reply_markup=invite_role_keyboard(),
    )


# ==== Rol tanlash ====
@router.callback_query(CreateInviteFSM.role, F.data.startswith("invite_role:"))
async def process_invite_role(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Rolni tanlash."""
    role = callback.data.split(":")[1]
    await callback.answer()

    await state.update_data(role=role)
    role_name = ROLE_NAMES.get(role, role)

    if role == "worker":
        # Worker uchun step so'raymiz
        await state.set_state(CreateInviteFSM.step_number)
        await callback.message.edit_text(
            f"✅ Rol: <b>{role_name}</b>\n\n"
            f"2️⃣ <b>Qaysi bo'lim uchun?</b>",
            reply_markup=invite_step_keyboard(),
        )
    else:
        # QC yoki Admin — step kerak emas
        await state.update_data(step_number=None)
        await state.set_state(CreateInviteFSM.expires_in)
        await callback.message.edit_text(
            f"✅ Rol: <b>{role_name}</b>\n\n"
            f"3️⃣ <b>Havola qancha vaqt amal qiladi?</b>",
            reply_markup=invite_expires_keyboard(),
        )


# ==== Step tanlash ====
@router.callback_query(CreateInviteFSM.step_number, F.data.startswith("invite_step:"))
async def process_invite_step(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Stepni tanlash."""
    step_number = int(callback.data.split(":")[1])
    await callback.answer()

    await state.update_data(step_number=step_number)
    step_name = STEP_NAMES.get(step_number, str(step_number))
    await state.set_state(CreateInviteFSM.expires_in)

    await callback.message.edit_text(
        f"✅ Bo'lim: <b>{step_name}</b>\n\n"
        f"3️⃣ <b>Havola qancha vaqt amal qiladi?</b>",
        reply_markup=invite_expires_keyboard(),
    )


# ==== Muddat tanlash ====
@router.callback_query(CreateInviteFSM.expires_in, F.data.startswith("invite_expires:"))
async def process_invite_expires(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Muddatni tanlash."""
    value = callback.data.split(":")[1]
    await callback.answer()

    if value == "none":
        expires_in_hours = None
        expires_text = "♾ Cheksiz"
    else:
        expires_in_hours = int(value)
        if expires_in_hours == 1:
            expires_text = "🕐 1 soat"
        elif expires_in_hours == 24:
            expires_text = "📅 1 kun"
        elif expires_in_hours == 168:
            expires_text = "📅 7 kun"
        elif expires_in_hours == 720:
            expires_text = "📅 30 kun"
        else:
            expires_text = f"{expires_in_hours} soat"

    await state.update_data(expires_in_hours=expires_in_hours)
    await state.set_state(CreateInviteFSM.max_uses)

    await callback.message.edit_text(
        f"✅ Muddat: <b>{expires_text}</b>\n\n"
        f"4️⃣ <b>Necha marta ishlatilishi mumkin?</b>",
        reply_markup=invite_max_uses_keyboard(),
    )


# ==== Ishlatish soni ====
@router.callback_query(CreateInviteFSM.max_uses, F.data.startswith("invite_max_uses:"))
async def process_invite_max_uses(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Ishlatish sonini tanlash."""
    max_uses = int(callback.data.split(":")[1])
    await callback.answer()

    await state.update_data(max_uses=max_uses)
    await state.set_state(CreateInviteFSM.confirm)

    await _show_invite_confirmation(callback.message, state)


# ==== Tasdiqlash ====
@router.callback_query(CreateInviteFSM.confirm, F.data == "invite_confirm")
async def confirm_create_invite(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User,
):
    """Invite ni DB ga saqlash."""
    data = await state.get_data()
    await callback.answer()

    invite = await create_invite(
        session=session,
        role=data["role"],
        step_number=data.get("step_number"),
        created_by=user.telegram_id,
        expires_in_hours=data.get("expires_in_hours"),
        max_uses=data.get("max_uses", 1),
    )

    await state.clear()

    link = f"https://t.me/{settings.BOT_USERNAME}?start={invite.code}"

    text = (
        f"✅ <b>Havola yaratildi!</b>\n\n"
        f"🎭 Rol: {ROLE_NAMES.get(invite.role, invite.role)}\n"
    )

    if invite.step_number:
        step_name = STEP_NAMES.get(invite.step_number, invite.step_number)
        text += f"🔧 Bo'lim: {step_name}\n"

    text += f"\n🔗 <b>Havola:</b>\n<code>{link}</code>\n\n"
    text += f"<i>Havolani nusxalash uchun bosing yoki uzoq bosing.</i>"

    await callback.message.edit_text(
        text,
        reply_markup=invite_detail_keyboard(invite, settings.BOT_USERNAME),
    )


# ==== Qaytadan ====
@router.callback_query(CreateInviteFSM.confirm, F.data == "invite_restart")
async def restart_create_invite(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Boshidan boshlash."""
    await callback.answer()
    await state.clear()
    await state.set_state(CreateInviteFSM.role)

    await callback.message.edit_text(
        "➕ <b>Yangi invite link yaratish</b>\n\n"
        "1️⃣ <b>Rolni tanlang:</b>",
        reply_markup=invite_role_keyboard(),
    )


# ==== Bekor qilish ====
@router.callback_query(F.data == "invite_cancel")
async def cancel_create_invite(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    """Bekor qilish."""
    await callback.answer("❌ Bekor qilindi")
    await state.clear()

    # Invite ro'yxatiga qaytamiz
    invites = await get_active_invites(session)

    if not invites:
        text = (
            "🔗 <b>Invite linklar</b>\n\n"
            "Hozircha faol havolalar yo'q."
        )
    else:
        text = (
            f"🔗 <b>Invite linklar</b>\n\n"
            f"Faol havolalar: <b>{len(invites)}</b> ta"
        )

    await callback.message.edit_text(
        text,
        reply_markup=invites_list_keyboard(invites, settings.BOT_USERNAME),
    )


# ==== Yordamchi ====
async def _show_invite_confirmation(message: Message, state: FSMContext) -> None:
    """Tasdiqlash oynasini ko'rsatish."""
    data = await state.get_data()

    role_name = ROLE_NAMES.get(data["role"], data["role"])
    step_text = "—"
    if data.get("step_number"):
        step_text = STEP_NAMES.get(data["step_number"], str(data["step_number"]))

    # Muddat
    expires_in = data.get("expires_in_hours")
    if expires_in is None:
        expires_text = "♾ Cheksiz"
    elif expires_in == 1:
        expires_text = "🕐 1 soat"
    elif expires_in == 24:
        expires_text = "📅 1 kun"
    elif expires_in == 168:
        expires_text = "📅 7 kun"
    elif expires_in == 720:
        expires_text = "📅 30 kun"
    else:
        expires_text = f"{expires_in} soat"

    # Ishlatish soni
    max_uses = data.get("max_uses", 1)
    max_uses_text = "♾ Cheksiz" if max_uses == 0 else f"{max_uses} marta"

    text = (
        f"📋 <b>Tasdiqlash</b>\n\n"
        f"🎭 Rol: {role_name}\n"
        f"🔧 Bo'lim: {step_text}\n"
        f"⏰ Muddat: {expires_text}\n"
        f"🔢 Ishlatish: {max_uses_text}\n\n"
        f"<b>Havola yaratilsinmi?</b>"
    )

    await message.edit_text(
        text,
        reply_markup=invite_confirm_keyboard(),
    )
