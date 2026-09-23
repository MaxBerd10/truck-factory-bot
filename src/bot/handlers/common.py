"""/start, /help va umumiy handlerlar."""
from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards import main_menu_keyboard
from src.bot.keyboards.language import language_keyboard
from src.database.models.user import User
from src.services.i18n_service import (
    _,
    get_role_name,
    get_step_name,
)
from src.services.user_service import create_admin_if_needed


router = Router(name="common")


# ==== /start (deep link siz) ====
@router.message(CommandStart(deep_link=False))
async def cmd_start(
    message: Message,
    user: User | None,
    session,
):
    """Start buyrug'i."""
    tg_user = message.from_user

    if user:
        # Til tanlanmagan bo'lsa — so'rash
        if not user.language:
            await message.answer(
                "🌐 <b>Tilni tanlang</b>\n\n"
                "🇺🇿 O'zbekcha (lotin)\n"
                "🇺🇿 Ўзбекча (кирилл)\n"
                "🇷🇺 Русский",
                reply_markup=language_keyboard(),
            )
            return

        await show_main_menu(message, user)
        return

    # Yangi foydalanuvchi — admin yaratish
    admin = await create_admin_if_needed(
        session=session,
        telegram_id=tg_user.id,
        full_name=tg_user.full_name,
        username=tg_user.username,
    )

    if admin:
        await message.answer(
            _(
                "start.admin_welcome",
                language=admin.language or "uz",
                name=admin.full_name,
            ),
            reply_markup=main_menu_keyboard(admin.role),
        )
        return

    await message.answer(
        _("start.no_access", language="uz"),
    )


# ==== /help ====
@router.message(Command("help"))
async def cmd_help(message: Message, user: User | None):
    """Yordam."""
    if not user:
        await message.answer(
            "Yordam olish uchun administratorga murojaat qiling."
        )
        return

    lang = user.language or "uz"

    help_text = (
        f"📖 <b>{_('common.help', language=lang)}</b>\n\n"
        f"<b>Buyruqlar:</b>\n"
        f"/start — {_('common.main_menu', language=lang)}\n"
        f"/help — {_('common.help', language=lang)}\n"
        f"/id — Telegram ID\n"
    )

    if user.is_admin:
        help_text += "\n<b>Admin buyruqlari:</b>\n/admin — Admin panel\n"

    await message.answer(help_text)


# ==== /id ====
@router.message(Command("id"))
async def cmd_id(message: Message):
    """Telegram ID ni ko'rsatish."""
    username = message.from_user.username or "yo'q"
    await message.answer(
        f"🆔 Sizning Telegram ID: <code>{message.from_user.id}</code>\n"
        f"👤 Ism: {message.from_user.full_name}\n"
        f"📛 Username: @{username}"
    )


# ==== 🏠 Asosiy menyu (reply tugma) ====
@router.message(F.text == "🏠 Asosiy menyu")
async def btn_main_menu(message: Message, user: User | None):
    """Reply tugmadan asosiy menyuga qaytish."""
    if not user:
        await message.answer("Ruxsat yo'q.")
        return
    await show_main_menu(message, user)


# ==== 🔙 Asosiy menyu (inline callback) ====
@router.callback_query(F.data == "main_menu")
async def callback_main_menu(
    callback: CallbackQuery,
    user: User | None,
):
    """Inline tugmadan asosiy menyuga qaytish."""
    await callback.answer()

    if not user:
        await callback.message.answer("Ruxsat yo'q.")
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    lang = user.language or "uz"
    role_name = get_role_name(user.role, lang)

    text = f"🏠 <b>{_('common.main_menu', language=lang)}</b>\n\n"
    text += f"👋 <b>{user.full_name}</b>\n"
    text += f"🎭 {_('start.role', language=lang, role=role_name)}\n"

    if user.step_number:
        step_name = get_step_name(user.step_number, lang)
        text += f"{_('start.step', language=lang, step=step_name)}\n"

    await callback.message.answer(
        text,
        reply_markup=main_menu_keyboard(user.role),
    )


# ==== Yordamchi funksiya ====
async def show_main_menu(message: Message, user: User) -> None:
    """Rolga qarab asosiy menyu ko'rsatish."""
    lang = user.language or "uz"
    role_name = get_role_name(user.role, lang)

    text = f"👋 <b>{user.full_name}</b>\n\n"
    text += f"🎭 {_('start.role', language=lang, role=role_name)}\n"

    if user.step_number:
        step_name = get_step_name(user.step_number, lang)
        text += f"{_('start.step', language=lang, step=step_name)}\n"

    text += f"\n{_('start.choose_section', language=lang)}"

    await message.answer(
        text,
        reply_markup=main_menu_keyboard(user.role),
    )


# ==== Fallback (noma'lum matnli xabarlar) ====
@router.message(StateFilter(None), F.text & ~F.text.startswith("/"))
async def fallback_text(
    message: Message,
    user: User | None,
):
    """Noma'lum matnli xabarlar uchun."""
    if not user:
        return

    # Tugmalar ro'yxati
    known_buttons = {
        "📋 Vazifalarim", "📤 Ish yuborish", "📜 Tarixim",
        "📊 Statistika", "🔔 Sozlamalar", "🏠 Asosiy menyu",
        "🔔 Tekshirish navbati",
        "🚛 Trucklar", "👥 Foydalanuvchilar", "➕ Yangi truck",
        "🏆 Reyting", "📈 Grafik", "📤 Excel hisobot",
    }

    if message.text in known_buttons:
        return

    lang = user.language or "uz"

    await message.answer(
        _("common.unknown_command", language=lang),
        reply_markup=main_menu_keyboard(user.role),
    )
