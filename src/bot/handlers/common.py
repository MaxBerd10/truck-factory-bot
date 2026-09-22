"""/start, /help va umumiy handlerlar."""
from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards import main_menu_keyboard
from src.database.models.user import User
from src.services.user_service import create_admin_if_needed
from src.utils.constants import ROLE_NAMES, STEP_NAMES
from src.utils.logger import logger


router = Router(name="common")


# ==== /start (deep link siz) ====
@router.message(CommandStart(deep_link=False))
async def cmd_start(
    message: Message,
    user: User | None,
    session,
):
    """Start buyrug'i — foydalanuvchini tanish yoki admin yaratish."""
    tg_user = message.from_user

    if user:
        await show_main_menu(message, user)
        return

    admin = await create_admin_if_needed(
        session=session,
        telegram_id=tg_user.id,
        full_name=tg_user.full_name,
        username=tg_user.username,
    )

    if admin:
        await message.answer(
            f"👑 <b>Xush kelibsiz, {admin.full_name}!</b>\n\n"
            f"Siz <b>Administrator</b> sifatida tizimga kirdingiz.",
            reply_markup=main_menu_keyboard(admin.role),
        )
        return

    await message.answer(
        "🚫 <b>Ruxsat yo'q</b>\n\n"
        "Siz tizimda ro'yxatdan o'tmagansiz.\n\n"
        "Ishga qabul qilinish uchun <b>administratorga</b> murojaat qiling.\n"
        "Agar sizda <b>taklif havolasi</b> bo'lsa, uni bosing.",
    )


# ==== /help ====
@router.message(Command("help"))
async def cmd_help(message: Message, user: User | None):
    """Yordam."""
    if not user:
        await message.answer("Yordam olish uchun administratorga murojaat qiling.")
        return

    help_text = (
        "📖 <b>Yordam</b>\n\n"
        "<b>Buyruqlar:</b>\n"
        "/start — Asosiy menyu\n"
        "/help — Yordam\n"
        "/id — Telegram ID ingizni ko'rish\n"
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
        await message.answer("Ruxsat yo'q. Administratorga murojaat qiling.")
        return
    await show_main_menu(message, user)


# ==== 🔙 Asosiy menyu (inline callback) — HAMMA UCHUN ====
@router.callback_query(F.data == "main_menu")
async def callback_main_menu(
    callback: CallbackQuery,
    user: User | None,
):
    """Inline tugmadan asosiy menyuga qaytish (hamma rollar uchun)."""
    await callback.answer()

    if not user:
        await callback.message.answer("Ruxsat yo'q.")
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    role_name = ROLE_NAMES.get(user.role, user.role)

    text = f"🏠 <b>Asosiy menyu</b>\n\n"
    text += f"👋 Salom, <b>{user.full_name}</b>!\n"
    text += f"🎭 Rol: {role_name}\n"

    if user.step_number:
        step_name = STEP_NAMES.get(user.step_number, f"Step {user.step_number}")
        text += f"🔧 Bo'lim: {step_name}\n"

    await callback.message.answer(
        text,
        reply_markup=main_menu_keyboard(user.role),
    )


# ==== Yordamchi funksiya ====
async def show_main_menu(message: Message, user: User) -> None:
    """Rolga qarab asosiy menyu ko'rsatish."""
    role_name = ROLE_NAMES.get(user.role, user.role)

    text = f"👋 Salom, <b>{user.full_name}</b>!\n\n"
    text += f"🎭 Rol: {role_name}\n"

    if user.step_number:
        step_name = STEP_NAMES.get(user.step_number, f"Step {user.step_number}")
        text += f"🔧 Bo'lim: {step_name}\n"

    text += "\nKerakli bo'limni tanlang:"

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

    await message.answer(
        "🤔 <b>Buyruq tushunarsiz</b>\n\n"
        "Iltimos, pastdagi tugmalardan foydalaning.\n\n"
        "💡 <i>Yordam kerak bo'lsa /help buyrug'ini yuboring.</i>",
        reply_markup=main_menu_keyboard(user.role),
    )
