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
    if telegram_id not in settings.ADMIN_IDS:
        return None

    existing = await get_user_by_telegram_id(session, telegram_id)
    if existing:
        if existing.role != UserRole.ADMIN:
            existing.role = UserRole.ADMIN
            await session.flush()
        return existing

    admin = User(
        telegram_id=telegram_id,
        full_name=full_name,
        username=username,
        role=UserRole.ADMIN,
        is_active=True,
        language="uz",
    )
    session.add(admin)
    await session.flush()

    logger.info(f"👑 Admin yaratildi: {full_name} (id={telegram_id})")
    return admin


async def create_user_from_invite(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    role: str,
    step_number: int | None = None,
    phone: str | None = None,
    created_by: int | None = None,
    username: str | None = None,
    language: str = "uz",
) -> User:
    """Invite yoki admin tomonidan foydalanuvchi yaratish.

    Args:
        session: DB sessiya
        telegram_id: Telegram ID
        full_name: To'liq ism
        role: Rol (worker, qc, admin)
        step_number: Step raqami (faqat worker uchun)
        phone: Telefon raqami
        created_by: Kim yaratgan (Telegram ID)
        username: Telegram username
        language: Til kodi (uz, uz_cyrl, ru)

    Returns:
        User: Yaratilgan foydalanuvchi
    """
    user = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        role=role,
        step_number=step_number,
        phone=phone,
        created_by=created_by,
        is_active=True,
        language=language,
    )
    session.add(user)
    await session.flush()

    logger.info(
        f"👤 Yangi user yaratildi: {full_name} (@{username}), "
        f"role={role}, step={step_number}"
    )

    return user
