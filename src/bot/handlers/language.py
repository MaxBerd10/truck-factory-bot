"""Til tanlash handler."""
from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.language import (
    language_settings_keyboard,
)
from src.database.models.user import User
from src.services.i18n_service import (
    _,
    get_role_name,
    get_step_name,
)


router = Router(name="language")


# ==== /start da til tanlash ====
@router.callback_query(F.data.startswith("lang:"))
async def choose_language(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Til tanlash (/start da)."""
    lang = callback.data.split(":")[1]

    # Tilni saqlash
    user.language = lang
    await session.flush()

    # Til nomini olish (o'zi tanlagan tilda)
    lang_name = _(
        f"language.{lang}",
        language=lang,
    )

    await callback.answer(
        _("language.changed", language=lang, language_name=lang_name)
    )

    # Asosiy menyu (yangi tilda)
    await _show_main_menu(callback, user, lang)


# ==== Sozlamalarda til o'zgartirish ====
@router.callback_query(F.data.startswith("lang_set:"))
async def change_language_settings(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Sozlamalarda til o'zgartirish."""
    lang = callback.data.split(":")[1]

    user.language = lang
    await session.flush()

    lang_name = _(
        f"language.{lang}",
        language=lang,
    )

    await callback.answer(
        _("language.changed", language=lang, language_name=lang_name)
    )

    # Asosiy menyu (yangi tilda)
    await _show_main_menu(callback, user, lang)


# ==== Sozlamalarda "Til" tugmasi ====
@router.callback_query(F.data == "settings_language")
async def show_language_settings(
    callback: CallbackQuery,
    user: User,
):
    """Til tanlash (sozlamalarda)."""
    await callback.answer()

    lang = user.language or "uz"

    await callback.message.edit_text(
        f"{_('language.title', language=lang)}\n\n"
        f"{_('language.choose', language=lang)}",
        reply_markup=language_settings_keyboard(),
    )


# ==== Yordamchi ====
async def _show_main_menu(
    callback: CallbackQuery,
    user: User,
    lang: str,
) -> None:
    """Asosiy menyuni ko'rsatish (yangi tilda)."""
    role_name = get_role_name(user.role, lang)

    text = f"👋 <b>{user.full_name}</b>\n\n"
    text += f"🎭 {_('start.role', language=lang, role=role_name)}\n"

    if user.step_number:
        step_name = get_step_name(user.step_number, lang)
        text += f"{_('start.step', language=lang, step=step_name)}\n"

    text += f"\n{_('start.choose_section', language=lang)}"

    await callback.message.edit_text(text)
