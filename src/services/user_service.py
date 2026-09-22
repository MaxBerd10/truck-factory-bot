"""Foydalanuvchi bilan ishlash servisi."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database.models.user import User
from src.utils.constants import UserRole
from src.utils.logger import logger


async def get_user_by_telegram_id(
    session: AsyncSession,
    telegram_id: int,
) -> User | None:
    """Telegram ID bo'yicha foydalanuvchini topish."""
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_admin_if_needed(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    username: str | None,
) -> User | None:
    """Agar foydalanuvchi ADMIN_IDS da bo'lsa va DB da yo'q bo'lsa — yaratadi.

    Returns:
        User | None: Yaratilgan yoki mavjud user, yoki None.
    """
    # ADMIN_IDS da bormi?
    if telegram_id not in settings.ADMIN_IDS:
        return None

    # DB da bormi?
    existing = await get_user_by_telegram_id(session, telegram_id)
    if existing:
        return existing

    # Yangi admin yaratamiz
    new_admin = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        role=UserRole.ADMIN.value,
        step_number=None,
        is_active=True,
        created_by=None,  # o'zi
    )
    session.add(new_admin)
    await session.flush()  # ID olish uchun

    logger.success(
        f"👑 Yangi admin yaratildi: {full_name} (@{username}), "
        f"telegram_id={telegram_id}"
    )

    return new_admin


async def create_user_from_invite(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    username: str | None,
    role: str,
    step_number: int | None = None,
    created_by: int | None = None,
) -> User:
    """Invite orqali foydalanuvchi yaratish."""
    user = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        role=role,
        step_number=step_number,
        is_active=True,
        created_by=created_by,
    )
    session.add(user)
    await session.flush()

    logger.success(
        f"👤 Yangi user yaratildi: {full_name} (@{username}), "
        f"role={role}, step={step_number}"
    )

    return user
