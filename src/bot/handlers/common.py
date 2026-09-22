"""/start, /help va umumiy handlerlar."""
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from src.bot.keyboards import main_menu_keyboard, start_keyboard
from src.database.models.user import User
from src.services.user_service import create_admin_if_needed
from src.utils.constants import ROLE_NAMES, STEP_NAMES
from src.utils.logger import logger


router = Router(name="common")


# ==== /start ====
@router.message(CommandStart())
async def cmd_start(
    message: Message,
    user: User | None,
    session,
):
    """Start buyrug'i — foydalanuvchini tanish yoki admin yaratish."""
    tg_user = message.from_user

    # 1. Agar ro'yxatdan o'tgan bo'lsa — menyu
    if user:
        await show_main_menu(message, user)
        return

    # 2. Adminmi? Avtomatik yaratamiz
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

    # 3. Ro'yxatdan o'tmagan
    await message.answer(
        "🚫 <b>Ruxsat yo'q</b>\n\n"
        "Siz tizimda ro'yxatdan o'tmagansiz.\n\n"
        "Ishga qabul qilinish uchun <b>administratorga</b> murojaat qiling.\n"
        "Agar sizda <b>taklif havolasi</b> bo'lsa, uni bosing.",
        reply_markup=None,
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

    help_text = (
        "📖 <b>Yordam</b>\n\n"
        "<b>Buyruqlar:</b>\n"
        "/start — Asosiy menyu\n"
        "/help — Yordam\n"
        "/id — Telegram ID ingizni ko'rish\n"
    )

    if user.is_admin:
        help_text += (
            "\n<b>Admin buyruqlari:</b>\n"
            "/admin — Admin panel\n"
        )

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


# ==== Asosiy menyu tugmasi ====
@router.message(F.text == "🏠 Asosiy menyu")
async def btn_main_menu(message: Message, user: User | None):
    """Asosiy menyuga qaytish."""
    if not user:
        await message.answer("Ruxsat yo'q. Administratorga murojaat qiling.")
        return
    await show_main_menu(message, user)


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
