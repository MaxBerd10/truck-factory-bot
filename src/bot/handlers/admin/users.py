"""Admin — foydalanuvchilar boshqaruvi."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsAdmin
from src.bot.keyboards.admin import user_detail_keyboard, users_list_keyboard
from src.database.models.user import User
from src.utils.constants import ROLE_NAMES, STEP_NAMES
from src.utils.logger import logger


router = Router(name="admin_users")


# ==== Foydalanuvchilar bo'limi (reply tugma) ====
@router.message(IsAdmin(), F.text == "👥 Foydalanuvchilar")
async def show_users_menu(message: Message, session: AsyncSession):
    """Foydalanuvchilar ro'yxatini ko'rsatish."""
    await _send_users_list(message, session, page=0)


# ==== Sahifalash ====
@router.callback_query(IsAdmin(), F.data.startswith("users_page:"))
async def paginate_users(
    callback: CallbackQuery,
    session: AsyncSession,
):
    """Sahifani almashtirish."""
    page = int(callback.data.split(":")[1])
    await callback.answer()
    await _edit_users_list(callback, session, page)


# ==== Bitta userni ko'rish ====
@router.callback_query(IsAdmin(), F.data.startswith("user_view:"))
async def view_user(
    callback: CallbackQuery,
    session: AsyncSession,
):
    """Bitta userni ko'rish."""
    user_id = int(callback.data.split(":")[1])

    target_user = await session.get(User, user_id)
    if not target_user:
        await callback.answer("❌ Foydalanuvchi topilmadi", show_alert=True)
        return

    await callback.answer()

    role_name = ROLE_NAMES.get(target_user.role, target_user.role)
    status = "✅ Faol" if target_user.is_active else "🚫 Bloklangan"
    username = target_user.username or "yo'q"

    text = (
        f"👤 <b>{target_user.full_name}</b>\n\n"
        f"🆔 ID: <code>{target_user.id}</code>\n"
        f"📱 Telegram ID: <code>{target_user.telegram_id}</code>\n"
        f"📛 Username: @{username}\n"
        f"📞 Telefon: {target_user.phone or '—'}\n\n"
        f"🎭 Rol: {role_name}\n"
    )

    if target_user.step_number:
        step_name = STEP_NAMES.get(target_user.step_number, f"Step {target_user.step_number}")
        text += f"🔧 Bo'lim: {step_name}\n"

    text += f"\n📊 Holat: {status}\n"
    text += f"📅 Qo'shilgan: {target_user.created_at.strftime('%Y-%m-%d %H:%M')}"

    await callback.message.edit_text(
        text,
        reply_markup=user_detail_keyboard(target_user),
    )


# ==== Bloklash ====
@router.callback_query(IsAdmin(), F.data.startswith("user_block:"))
async def block_user(
    callback: CallbackQuery,
    session: AsyncSession,
    user: User,
):
    """Userni bloklash."""
    user_id = int(callback.data.split(":")[1])

    target_user = await session.get(User, user_id)
    if not target_user:
        await callback.answer("❌ Foydalanuvchi topilmadi", show_alert=True)
        return

    if target_user.id == user.id:
        await callback.answer("❌ O'zingizni bloklay olmaysiz!", show_alert=True)
        return

    if not target_user.is_active:
        await callback.answer("⚠️ Allaqachon bloklangan", show_alert=True)
        return

    target_user.is_active = False
    await session.flush()

    logger.info(
        f"🚫 User bloklandi: {target_user.full_name} (id={target_user.id}) "
        f"tomonidan {user.full_name}"
    )

    await callback.answer("🚫 Bloklandi")

    # Xabarni yangilash
    role_name = ROLE_NAMES.get(target_user.role, target_user.role)
    username = target_user.username or "yo'q"

    text = (
        f"👤 <b>{target_user.full_name}</b>\n\n"
        f"🆔 ID: <code>{target_user.id}</code>\n"
        f"📱 Telegram ID: <code>{target_user.telegram_id}</code>\n"
        f"📛 Username: @{username}\n"
        f"📞 Telefon: {target_user.phone or '—'}\n\n"
        f"🎭 Rol: {role_name}\n"
    )

    if target_user.step_number:
        step_name = STEP_NAMES.get(target_user.step_number, f"Step {target_user.step_number}")
        text += f"🔧 Bo'lim: {step_name}\n"

    text += "\n📊 Holat: 🚫 Bloklangan\n"
    text += f"📅 Qo'shilgan: {target_user.created_at.strftime('%Y-%m-%d %H:%M')}"

    await callback.message.edit_text(
        text,
        reply_markup=user_detail_keyboard(target_user),
    )


# ==== Aktivlashtirish ====
@router.callback_query(IsAdmin(), F.data.startswith("user_unblock:"))
async def unblock_user(
    callback: CallbackQuery,
    session: AsyncSession,
    user: User,
):
    """Userni aktivlashtirish."""
    user_id = int(callback.data.split(":")[1])

    target_user = await session.get(User, user_id)
    if not target_user:
        await callback.answer("❌ Foydalanuvchi topilmadi", show_alert=True)
        return

    if target_user.is_active:
        await callback.answer("⚠️ Allaqachon faol", show_alert=True)
        return

    target_user.is_active = True
    await session.flush()

    logger.info(
        f"✅ User aktivlashtirildi: {target_user.full_name} (id={target_user.id}) "
        f"tomonidan {user.full_name}"
    )

    await callback.answer("✅ Aktivlashtirildi")

    role_name = ROLE_NAMES.get(target_user.role, target_user.role)
    username = target_user.username or "yo'q"

    text = (
        f"👤 <b>{target_user.full_name}</b>\n\n"
        f"🆔 ID: <code>{target_user.id}</code>\n"
        f"📱 Telegram ID: <code>{target_user.telegram_id}</code>\n"
        f"📛 Username: @{username}\n"
        f"📞 Telefon: {target_user.phone or '—'}\n\n"
        f"🎭 Rol: {role_name}\n"
    )

    if target_user.step_number:
        step_name = STEP_NAMES.get(target_user.step_number, f"Step {target_user.step_number}")
        text += f"🔧 Bo'lim: {step_name}\n"

    text += "\n📊 Holat: ✅ Faol\n"
    text += f"📅 Qo'shilgan: {target_user.created_at.strftime('%Y-%m-%d %H:%M')}"

    await callback.message.edit_text(
        text,
        reply_markup=user_detail_keyboard(target_user),
    )


# ==== Noop ====
@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    """Hech nima qilmaydi."""
    await callback.answer()


# ==== Yordamchi funksiyalar ====
async def _get_users_page(
    session: AsyncSession,
    page: int,
    per_page: int = 10,
) -> tuple[list[User], int]:
    """Sahifadagi userlarni va jami sonini olish."""
    total_stmt = select(func.count(User.id))
    total_result = await session.execute(total_stmt)
    total = total_result.scalar() or 0

    offset = page * per_page
    stmt = (
        select(User)
        .order_by(User.is_active.desc(), User.id)
        .offset(offset)
        .limit(per_page)
    )
    result = await session.execute(stmt)
    users = list(result.scalars().all())

    return users, total


async def _send_users_list(
    message: Message,
    session: AsyncSession,
    page: int = 0,
) -> None:
    """Yangi xabar bilan userlar ro'yxatini yuborish."""
    users, total = await _get_users_page(session, page, per_page=10)

    if total == 0:
        await message.answer(
            "👥 <b>Foydalanuvchilar</b>\n\n"
            "Hozircha foydalanuvchilar yo'q.\n\n"
            "➕ Yangi qo'shish uchun quyidagi tugmani bosing.",
            reply_markup=users_list_keyboard([], page=0, total=0),
        )
        return

    text = (
        f"👥 <b>Foydalanuvchilar</b>\n\n"
        f"Jami: <b>{total}</b> ta\n"
        f"Sahifa: <b>{page + 1}</b>\n\n"
        f"Batafsil ko'rish uchun foydalanuvchini tanlang:"
    )

    await message.answer(
        text,
        reply_markup=users_list_keyboard(users, page=page, per_page=10, total=total),
    )


async def _edit_users_list(
    callback: CallbackQuery,
    session: AsyncSession,
    page: int = 0,
) -> None:
    """Mavjud xabarni tahrirlab, userlar ro'yxatini yangilash."""
    users, total = await _get_users_page(session, page, per_page=10)

    if total == 0:
        await callback.message.edit_text(
            "👥 <b>Foydalanuvchilar</b>\n\n"
            "Hozircha foydalanuvchilar yo'q.",
            reply_markup=users_list_keyboard([], page=0, total=0),
        )
        return

    text = (
        f"👥 <b>Foydalanuvchilar</b>\n\n"
        f"Jami: <b>{total}</b> ta\n"
        f"Sahifa: <b>{page + 1}</b>\n\n"
        f"Batafsil ko'rish uchun foydalanuvchini tanlang:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=users_list_keyboard(users, page=page, per_page=10, total=total),
    )
