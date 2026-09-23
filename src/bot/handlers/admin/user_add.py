"""Admin — Yangi foydalanuvchi qo'shish (FSM)."""
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
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
from src.services.i18n_service import _, get_role_name, get_step_name
from src.services.user_service import (
    create_user_from_invite,
    get_user_by_telegram_id,
)
from src.utils.logger import logger


router = Router(name="admin_user_add")


# ==================== Boshlash ====================
@router.callback_query(IsAdmin(), F.data == "user_add")
async def start_add_user(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Yangi foydalanuvchi qo'shishni boshlash."""
    lang = user.language or "uz"
    await callback.answer()
    await state.clear()
    await state.set_state(AddUserFSM.telegram_id)

    await callback.message.edit_text(
        _("admin.user_add_step1", language=lang),
        reply_markup=cancel_add_user_keyboard(lang),
    )


# ==================== Telegram ID ====================
@router.message(AddUserFSM.telegram_id, F.text)
async def process_telegram_id(
    message: Message,
    state: FSMContext,
    user: User,
    session: AsyncSession,
):
    """Telegram ID ni qabul qilish."""
    lang = user.language or "uz"
    text = message.text.strip()

    if not text.isdigit():
        await message.answer(
            _("admin.user_add_invalid_id", language=lang),
            reply_markup=cancel_add_user_keyboard(lang),
        )
        return

    telegram_id = int(text)

    existing = await get_user_by_telegram_id(session, telegram_id)
    if existing:
        await message.answer(
            _(
                "admin.user_add_exists",
                language=lang,
                name=existing.full_name,
            ),
            reply_markup=cancel_add_user_keyboard(lang),
        )
        return

    await state.update_data(telegram_id=telegram_id)
    await state.set_state(AddUserFSM.full_name)

    await message.answer(
        _("admin.user_add_step2", language=lang),
        reply_markup=cancel_add_user_keyboard(lang),
    )


# ==================== To'liq ism ====================
@router.message(AddUserFSM.full_name, F.text)
async def process_full_name(
    message: Message,
    state: FSMContext,
    user: User,
):
    """To'liq ismni qabul qilish."""
    lang = user.language or "uz"
    text = message.text.strip()

    if len(text) < 3:
        await message.answer(
            _("admin.user_add_name_short", language=lang),
            reply_markup=cancel_add_user_keyboard(lang),
        )
        return

    await state.update_data(full_name=text)
    await state.set_state(AddUserFSM.role)

    await message.answer(
        _("admin.user_add_step3", language=lang),
        reply_markup=role_choice_keyboard(lang),
    )


# ==================== Rol tanlash ====================
@router.callback_query(
    AddUserFSM.role,
    F.data.startswith("add_user_role:"),
)
async def process_role(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Rolni qabul qilish."""
    lang = user.language or "uz"
    role = callback.data.split(":")[1]
    await callback.answer()

    await state.update_data(role=role)

    if role == "worker":
        await state.set_state(AddUserFSM.step_number)
        await callback.message.edit_text(
            _("admin.user_add_step4_worker", language=lang),
            reply_markup=step_choice_keyboard(lang),
        )
    else:
        await state.update_data(step_number=None)
        await state.set_state(AddUserFSM.phone)
        await callback.message.edit_text(
            _("admin.user_add_step4", language=lang),
            reply_markup=skip_phone_keyboard(lang),
        )


# ==================== Step tanlash ====================
@router.callback_query(
    AddUserFSM.step_number,
    F.data.startswith("add_user_step:"),
)
async def process_step(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Stepni qabul qilish."""
    lang = user.language or "uz"
    step_num = int(callback.data.split(":")[1])
    await callback.answer()

    await state.update_data(step_number=step_num)
    await state.set_state(AddUserFSM.phone)

    await callback.message.edit_text(
        _("admin.user_add_step4", language=lang),
        reply_markup=skip_phone_keyboard(lang),
    )


# ==================== Telefon ====================
@router.message(AddUserFSM.phone, F.text)
async def process_phone(
    message: Message,
    state: FSMContext,
    user: User,
):
    """Telefon raqamini qabul qilish."""
    lang = user.language or "uz"
    text = message.text.strip()

    # Telefon raqamini tekshirish (soddalashtirilgan)
    phone_pattern = re.compile(r"^\+?\d{9,15}$")
    if not phone_pattern.match(text.replace(" ", "").replace("-", "")):
        await message.answer(
            _("admin.user_add_invalid_phone", language=lang),
            reply_markup=skip_phone_keyboard(lang),
        )
        return

    await state.update_data(phone=text)
    await state.set_state(AddUserFSM.confirm)

    await _show_confirmation(message, state, user, use_edit=False)


# ==================== Telefonni o'tkazib yuborish ====================
@router.callback_query(
    AddUserFSM.phone,
    F.data == "user_add_skip_phone",
)
async def skip_phone(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Telefonni o'tkazib yuborish."""
    await callback.answer()
    await state.update_data(phone=None)
    await state.set_state(AddUserFSM.confirm)

    await _show_confirmation(callback.message, state, user, use_edit=True)


# ==================== Tasdiqlash ====================
@router.callback_query(AddUserFSM.confirm, F.data == "user_add_confirm")
async def confirm_add_user(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    session: AsyncSession,
):
    """Foydalanuvchini yaratish."""
    lang = user.language or "uz"
    data = await state.get_data()
    await callback.answer()

    try:
        new_user = await create_user_from_invite(
            session=session,
            telegram_id=data["telegram_id"],
            full_name=data["full_name"],
            role=data["role"],
            step_number=data.get("step_number"),
            phone=data.get("phone"),
            created_by=user.telegram_id,
        )

        logger.info(
            f"➕ User yaratildi: {new_user.full_name} "
            f"(role={new_user.role}) tomonidan {user.full_name}"
        )

        await state.clear()

        role_name = get_role_name(new_user.role, lang)

        text = (
            f"✅ <b>{_('admin.user_add_created', language=lang)}</b>\n\n"
            f"👤 <b>{new_user.full_name}</b>\n"
            f"🆔 <code>{new_user.telegram_id}</code>\n"
            f"🎭 {role_name}\n"
        )

        if new_user.step_number:
            step_name = get_step_name(new_user.step_number, lang)
            text += f"🔧 {step_name}\n"

        text += f"\n<i>{_('admin.user_add_hint', language=lang)}</i>"

        await callback.message.edit_text(text)

    except Exception as e:
        logger.exception(f"❌ User yaratishda xato: {e}")
        await state.clear()
        await callback.message.edit_text(
            _("common.error_generic", language=lang)
        )


# ==================== Qaytadan ====================
@router.callback_query(AddUserFSM.confirm, F.data == "user_add_restart")
async def restart_add_user(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Boshidan boshlash."""
    lang = user.language or "uz"
    await callback.answer()
    await state.clear()
    await state.set_state(AddUserFSM.telegram_id)

    await callback.message.edit_text(
        _("admin.user_add_step1", language=lang),
        reply_markup=cancel_add_user_keyboard(lang),
    )


# ==================== Bekor qilish ====================
@router.callback_query(F.data == "user_add_cancel")
async def cancel_add_user(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Bekor qilish."""
    lang = user.language or "uz"
    await callback.answer(_("common.cancel", language=lang))
    await state.clear()

    await callback.message.edit_text(
        _("common.cancelled", language=lang),
    )


# ==================== Yordamchi ====================
async def _show_confirmation(
    message: Message,
    state: FSMContext,
    user: User,
    use_edit: bool = True,
) -> None:
    """Tasdiqlash oynasini ko'rsatish."""
    lang = user.language or "uz"
    data = await state.get_data()

    role_name = get_role_name(data.get("role", "worker"), lang)

    text = (
        f"📋 <b>{_('common.confirm', language=lang)}</b>\n\n"
        f"👤 <b>{data.get('full_name')}</b>\n"
        f"🆔 <code>{data.get('telegram_id')}</code>\n"
        f"🎭 {role_name}\n"
    )

    if data.get("step_number"):
        step_name = get_step_name(data["step_number"], lang)
        text += f"🔧 {step_name}\n"

    if data.get("phone"):
        text += f"📞 {data['phone']}\n"

    text += f"\n<b>{_('admin.user_add_confirm_question', language=lang)}</b>"

    keyboard = confirm_add_user_keyboard(lang)

    if use_edit:
        try:
            await message.edit_text(text, reply_markup=keyboard)
        except Exception:
            await message.answer(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)
