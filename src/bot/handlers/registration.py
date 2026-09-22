"""Invite orqali ro'yxatdan o'tish."""
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import (
    main_menu_keyboard,
    registration_confirm_keyboard,
    registration_skip_phone_keyboard,
)
from src.bot.keyboards.registration import registration_skip_phone_keyboard
from src.bot.states import RegistrationFSM
from src.config import settings
from src.database.models.user import User
from src.services.invite_service import get_invite_by_code, use_invite
from src.services.user_service import create_user_from_invite, get_user_by_telegram_id
from src.utils.constants import ROLE_NAMES, STEP_NAMES
from src.utils.logger import logger


router = Router(name="registration")


# ==== /start inv_xxx ====
@router.message(CommandStart(deep_link=True))
async def start_with_invite(
    message: Message,
    command: CommandStart,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
):
    """Deep link orqali /start."""
    # Agar allaqachon ro'yxatdan o'tgan bo'lsa
    if user:
        await message.answer(
            "Siz allaqachon ro'yxatdan o'tgansiz.",
            reply_markup=main_menu_keyboard(user.role),
        )
        return

    invite_code = command.args  # inv_xxx

    # Invite ni tekshirish
    invite = await get_invite_by_code(session, invite_code)

    if not invite:
        await message.answer(
            "❌ <b>Havola topilmadi</b>\n\n"
            "Bu havola mavjud emas yoki o'chirilgan.\n"
            "Administratorga murojaat qiling."
        )
        return

    if invite.is_used:
        await message.answer(
            "❌ <b>Havola allaqachon ishlatilgan</b>\n\n"
            "Bu havola bir martalik edi.\n"
            "Yangi havola olish uchun administratorga murojaat qiling."
        )
        return

    if invite.is_expired:
        await message.answer(
            "❌ <b>Havola muddati o'tgan</b>\n\n"
            "Bu havolaning amal qilish muddati tugagan.\n"
            "Yangi havola olish uchun administratorga murojaat qiling."
        )
        return

    # FSM ni boshlash
    await state.clear()
    await state.update_data(invite_code=invite_code, invite_id=invite.id)
    await state.set_state(RegistrationFSM.full_name)

    role_name = ROLE_NAMES.get(invite.role, invite.role)
    step_text = ""
    if invite.step_number:
        step_name = STEP_NAMES.get(invite.step_number, invite.step_number)
        step_text = f"\n🔧 Bo'lim: <b>{step_name}</b>"

    await message.answer(
        f"🎉 <b>Xush kelibsiz!</b>\n\n"
        f"Sizni <b>{role_name}</b> sifatida{step_text} "
        f"qo'shmoqchimiz.\n\n"
        f"1️⃣ <b>Ism familiyangizni kiriting:</b>\n\n"
        f"<i>Masalan: Akmal Karimov</i>"
    )


# ==== Ism familiya ====
@router.message(RegistrationFSM.full_name, F.text)
async def process_full_name(
    message: Message,
    state: FSMContext,
):
    """Ism familiyani qabul qilish."""
    text = message.text.strip()

    if len(text) < 3 or len(text) > 100:
        await message.answer(
            "❌ <b>Xato!</b>\n\n"
            "Ism familiya 3 dan 100 belgigacha bo'lishi kerak.\n"
            "Qaytadan kiriting:",
        )
        return

    await state.update_data(full_name=text)
    await state.set_state(RegistrationFSM.phone)

    await message.answer(
        f"✅ Ism: <b>{text}</b>\n\n"
        f"2️⃣ <b>Telefon raqamingizni kiriting</b> (ixtiyoriy):\n\n"
        f"<i>Masalan: +998901234567</i>",
        reply_markup=registration_skip_phone_keyboard(),
    )


# ==== Telefon (o'tkazib yuborish) ====
@router.callback_query(RegistrationFSM.phone, F.data == "reg_skip_phone")
async def skip_phone(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Telefon raqamni o'tkazib yuborish."""
    await callback.answer()
    await state.update_data(phone=None)
    await state.set_state(RegistrationFSM.confirm)

    await _show_registration_confirmation(callback.message, state)


# ==== Telefon kiritish ====
@router.message(RegistrationFSM.phone, F.text)
async def process_phone(
    message: Message,
    state: FSMContext,
):
    """Telefon raqamni qabul qilish."""
    text = message.text.strip()

    if len(text) < 7 or len(text) > 32:
        await message.answer(
            "❌ <b>Xato!</b>\n\n"
            "Telefon raqam 7 dan 32 belgigacha bo'lishi kerak.\n"
            "Qaytadan kiriting yoki o'tkazib yuboring:",
            reply_markup=registration_skip_phone_keyboard(),
        )
        return

    await state.update_data(phone=text)
    await state.set_state(RegistrationFSM.confirm)

    await _show_registration_confirmation(message, state)


# ==== Tasdiqlash ====
@router.callback_query(RegistrationFSM.confirm, F.data == "reg_confirm")
async def confirm_registration(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
):
    """Ro'yxatdan o'tishni tasdiqlash va userni yaratish."""
    # Agar allaqachon ro'yxatdan o'tgan bo'lsa
    if user:
        await callback.answer("Siz allaqachon ro'yxatdan o'tgansiz.", show_alert=True)
        await state.clear()
        return

    data = await state.get_data()
    await callback.answer()

    invite_code = data.get("invite_code")
    invite = await get_invite_by_code(session, invite_code)

    if not invite or invite.is_used or invite.is_expired:
        await callback.message.edit_text(
            "❌ <b>Xato!</b>\n\n"
            "Havola endi ishlamaydi. Administratorga murojaat qiling."
        )
        await state.clear()
        return

    # Yangi user yaratamiz
    tg_user = callback.from_user
    new_user = await create_user_from_invite(
        session=session,
        telegram_id=tg_user.id,
        full_name=data["full_name"],
        username=tg_user.username,
        role=invite.role,
        step_number=invite.step_number,
        created_by=invite.created_by,
    )

    # Telefon bo'lsa, qo'shamiz
    if data.get("phone"):
        new_user.phone = data["phone"]

    # Invite ni ishlatilgan deb belgilash
    await use_invite(session, invite, used_by_telegram_id=tg_user.id)

    await state.clear()

    role_name = ROLE_NAMES.get(new_user.role, new_user.role)
    step_text = ""
    if new_user.step_number:
        step_name = STEP_NAMES.get(new_user.step_number, new_user.step_number)
        step_text = f"\n🔧 Bo'lim: <b>{step_name}</b>"

    await callback.message.edit_text(
        f"🎉 <b>Ro'yxatdan o'tdingiz!</b>\n\n"
        f"👤 Ism: <b>{new_user.full_name}</b>\n"
        f"🎭 Rol: {role_name}{step_text}\n\n"
        f"Endi ishni boshlashingiz mumkin."
    )

    # Asosiy menyu ko'rsatamiz (yangi xabar bilan)
    await callback.message.answer(
        "🏠 <b>Asosiy menyu</b>",
        reply_markup=main_menu_keyboard(new_user.role),
    )


# ==== Qaytadan ====
@router.callback_query(RegistrationFSM.confirm, F.data == "reg_restart")
async def restart_registration(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Boshidan boshlash."""
    await callback.answer()
    await state.set_state(RegistrationFSM.full_name)

    await callback.message.edit_text(
        "1️⃣ <b>Ism familiyangizni kiriting:</b>\n\n"
        "<i>Masalan: Akmal Karimov</i>"
    )


# ==== Bekor qilish ====
@router.callback_query(F.data == "reg_cancel")
async def cancel_registration(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Ro'yxatdan o'tishni bekor qilish."""
    await callback.answer("❌ Bekor qilindi")
    await state.clear()

    await callback.message.edit_text(
        "❌ <b>Ro'yxatdan o'tish bekor qilindi.</b>\n\n"
        "Havolani yana bosib, qaytadan urinib ko'rishingiz mumkin."
    )


# ==== Yordamchi ====
async def _show_registration_confirmation(message: Message, state: FSMContext) -> None:
    """Tasdiqlash oynasini ko'rsatish."""
    data = await state.get_data()

    phone = data.get("phone") or "—"

    text = (
        f"📋 <b>Tasdiqlash</b>\n\n"
        f"👤 Ism: <b>{data['full_name']}</b>\n"
        f"📞 Telefon: {phone}\n\n"
        f"<b>Ma'lumotlar to'g'rimi?</b>"
    )

    await message.edit_text(
        text,
        reply_markup=registration_confirm_keyboard(),
    )
