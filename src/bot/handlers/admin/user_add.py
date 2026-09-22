"""Admin — Yangi foydalanuvchi qo'shish (FSM)."""
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsAdmin
from src.bot.keyboards.admin import (
    cancel_add_user_keyboard,
    confirm_add_user_keyboard,
    role_choice_keyboard,
    skip_phone_keyboard,
    step_choice_keyboard,
)
from src.bot.states import AddUserFSM
from src.database.models.user import User
from src.services.user_service import create_user_from_invite, get_user_by_telegram_id
from src.utils.constants import ROLE_NAMES, STEP_NAMES
from src.utils.logger import logger


router = Router(name="admin_user_add")


# ==== Boshlash ====
@router.callback_query(IsAdmin(), F.data == "user_add")
async def start_add_user(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Yangi user qo'shishni boshlash."""
    await callback.answer()
    await state.clear()
    await state.set_state(AddUserFSM.telegram_id)

    await callback.message.edit_text(
        "➕ <b>Yangi foydalanuvchi qo'shish</b>\n\n"
        "1️⃣ <b>Telegram ID</b> ni kiriting:\n\n"
        "<i>Masalan: 123456789</i>\n"
        "<i>Foydalanuvchi ID sini @userinfobot dan olish mumkin.</i>",
        reply_markup=cancel_add_user_keyboard(),
    )


# ==== 1. Telegram ID ====
@router.message(AddUserFSM.telegram_id, F.text)
async def process_telegram_id(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    """Telegram ID ni qabul qilish."""
    text = message.text.strip()

    # Raqam ekanligini tekshirish
    if not re.fullmatch(r"\d{5,15}", text):
        await message.answer(
            "❌ <b>Xato!</b>\n\n"
            "Telegram ID faqat raqamlardan iborat bo'lishi kerak (5-15 xona).\n"
            "Qaytadan kiriting:",
        )
        return

    telegram_id = int(text)

    # Allaqachon bormi?
    existing = await get_user_by_telegram_id(session, telegram_id)
    if existing:
        await message.answer(
            f"⚠️ <b>Bu foydalanuvchi allaqachon mavjud!</b>\n\n"
            f"👤 {existing.full_name}\n"
            f"🎭 Rol: {ROLE_NAMES.get(existing.role, existing.role)}\n\n"
            f"Boshqa Telegram ID kiriting yoki bekor qiling:",
            reply_markup=cancel_add_user_keyboard(),
        )
        return

    await state.update_data(telegram_id=telegram_id)
    await state.set_state(AddUserFSM.full_name)

    await message.answer(
        f"✅ Telegram ID: <code>{telegram_id}</code>\n\n"
        f"2️⃣ <b>Ism familiya</b> ni kiriting:\n\n"
        f"<i>Masalan: Akmal Karimov</i>",
        reply_markup=cancel_add_user_keyboard(),
    )


# ==== 2. Ism familiya ====
@router.message(AddUserFSM.full_name, F.text)
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
    await state.set_state(AddUserFSM.phone)

    await message.answer(
        f"✅ Ism: <b>{text}</b>\n\n"
        f"3️⃣ <b>Telefon raqam</b> ni kiriting (ixtiyoriy):\n\n"
        f"<i>Masalan: +998901234567</i>",
        reply_markup=skip_phone_keyboard(),
    )


# ==== 3. Telefon (ixtiyoriy) ====
@router.callback_query(AddUserFSM.phone, F.data == "add_user_skip_phone")
async def skip_phone(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Telefon raqamni o'tkazib yuborish."""
    await callback.answer()
    await state.update_data(phone=None)
    await state.set_state(AddUserFSM.role)

    await callback.message.edit_text(
        "✅ Telefon: <i>o'tkazib yuborildi</i>\n\n"
        "4️⃣ <b>Rolni tanlang:</b>",
        reply_markup=role_choice_keyboard(),
    )


@router.message(AddUserFSM.phone, F.text)
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
            reply_markup=skip_phone_keyboard(),
        )
        return

    await state.update_data(phone=text)
    await state.set_state(AddUserFSM.role)

    await message.answer(
        f"✅ Telefon: <b>{text}</b>\n\n"
        f"4️⃣ <b>Rolni tanlang:</b>",
        reply_markup=role_choice_keyboard(),
    )


# ==== 4. Rol ====
@router.callback_query(AddUserFSM.role, F.data.startswith("add_user_role:"))
async def process_role(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Rolni tanlash."""
    role = callback.data.split(":")[1]
    await callback.answer()

    await state.update_data(role=role)
    role_name = ROLE_NAMES.get(role, role)

    # Agar worker bo'lsa — step so'raymiz
    if role == "worker":
        await state.set_state(AddUserFSM.step_number)
        await callback.message.edit_text(
            f"✅ Rol: <b>{role_name}</b>\n\n"
            f"5️⃣ <b>Qaysi bo'limda ishlaydi?</b>",
            reply_markup=step_choice_keyboard(),
        )
    else:
        # QC yoki Admin — step kerak emas
        await state.update_data(step_number=None)
        await state.set_state(AddUserFSM.confirm)
        await _show_confirmation(callback.message, state)


# ==== 5. Step (faqat worker uchun) ====
@router.callback_query(AddUserFSM.step_number, F.data.startswith("add_user_step:"))
async def process_step(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Stepni tanlash."""
    step_number = int(callback.data.split(":")[1])
    await callback.answer()

    await state.update_data(step_number=step_number)
    await state.set_state(AddUserFSM.confirm)

    await _show_confirmation(callback.message, state)


# ==== 6. Tasdiqlash ====
@router.callback_query(AddUserFSM.confirm, F.data == "add_user_confirm")
async def confirm_add_user(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User,
):
    """Userni DB ga saqlash."""
    data = await state.get_data()
    await callback.answer()

    # DB ga yozamiz
    new_user = await create_user_from_invite(
        session=session,
        telegram_id=data["telegram_id"],
        full_name=data["full_name"],
        username=None,
        role=data["role"],
        step_number=data.get("step_number"),
        created_by=user.telegram_id,
    )

    await state.clear()

    role_name = ROLE_NAMES.get(new_user.role, new_user.role)
    text = (
        f"✅ <b>Foydalanuvchi muvaffaqiyatli qo'shildi!</b>\n\n"
        f"👤 Ism: <b>{new_user.full_name}</b>\n"
        f"🆔 Telegram ID: <code>{new_user.telegram_id}</code>\n"
        f"🎭 Rol: {role_name}\n"
    )
    if new_user.step_number:
        text += f"🔧 Bo'lim: {STEP_NAMES.get(new_user.step_number, new_user.step_number)}\n"

    text += f"\n<i>Endi foydalanuvchi botga /start bossa, tizimga kiradi.</i>"

    await callback.message.edit_text(text)


# ==== Qaytadan ====
@router.callback_query(AddUserFSM.confirm, F.data == "add_user_restart")
async def restart_add_user(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Boshidan boshlash."""
    await callback.answer()
    await state.clear()
    await state.set_state(AddUserFSM.telegram_id)

    await callback.message.edit_text(
        "➕ <b>Yangi foydalanuvchi qo'shish</b>\n\n"
        "1️⃣ <b>Telegram ID</b> ni kiriting:",
        reply_markup=cancel_add_user_keyboard(),
    )


# ==== Bekor qilish ====
@router.callback_query(F.data == "add_user_cancel")
async def cancel_add_user(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Bekor qilish."""
    await callback.answer("❌ Bekor qilindi")
    await state.clear()

    await callback.message.edit_text(
        "❌ <b>Bekor qilindi.</b>\n\n"
        "Foydalanuvchilar ro'yxatiga qaytish uchun /start bosing."
    )


# ==== Yordamchi ====
async def _show_confirmation(message: Message, state: FSMContext) -> None:
    """Tasdiqlash oynasini ko'rsatish."""
    data = await state.get_data()

    role_name = ROLE_NAMES.get(data["role"], data["role"])
    phone = data.get("phone") or "—"
    step_text = "—"
    if data.get("step_number"):
        step_text = STEP_NAMES.get(data["step_number"], str(data["step_number"]))

    text = (
        f"📋 <b>Tasdiqlash</b>\n\n"
        f"🆔 Telegram ID: <code>{data['telegram_id']}</code>\n"
        f"👤 Ism: <b>{data['full_name']}</b>\n"
        f"📞 Telefon: {phone}\n"
        f"🎭 Rol: {role_name}\n"
    )

    if data.get("step_number"):
        text += f"🔧 Bo'lim: {step_text}\n"

    text += "\n<b>Ma'lumotlar to'g'rimi?</b>"

    await message.edit_text(
        text,
        reply_markup=confirm_add_user_keyboard(),
    )
