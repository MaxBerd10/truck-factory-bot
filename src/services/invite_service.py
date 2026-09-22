"""Invite link bilan ishlash servisi."""
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.invite import Invite
from src.utils.logger import logger


def generate_invite_code() -> str:
    """Unikal invite kod yaratish."""
    return f"inv_{secrets.token_urlsafe(12)}"


async def create_invite(
    session: AsyncSession,
    role: str,
    step_number: int | None,
    created_by: int,
    expires_in_hours: int | None = None,
    max_uses: int = 1,
) -> Invite:
    """Yangi invite yaratish."""
    code = generate_invite_code()

    while True:
        existing = await session.execute(
            select(Invite).where(Invite.code == code)
        )
        if not existing.scalar_one_or_none():
            break
        code = generate_invite_code()

    expires_at = None
    if expires_in_hours:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

    invite = Invite(
        code=code,
        role=role,
        step_number=step_number,
        created_by=created_by,
        expires_at=expires_at,
        is_used=False,
    )
    session.add(invite)
    await session.flush()

    logger.success(
        f"🔗 Invite yaratildi: {code} "
        f"(role={role}, step={step_number}, expires={expires_at})"
    )

    return invite


async def get_invite_by_code(
    session: AsyncSession,
    code: str,
) -> Invite | None:
    """Kod bo'yicha invite topish."""
    stmt = select(Invite).where(Invite.code == code)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_active_invites(
    session: AsyncSession,
    limit: int = 50,
) -> list[Invite]:
    """Faol (ishlatilmagan va muddati o'tmagan) invite larni olish."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(Invite)
        .where(Invite.is_used == False)  # noqa: E712
        .where(
            (Invite.expires_at.is_(None)) | (Invite.expires_at > now)
        )
        .order_by(Invite.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def use_invite(
    session: AsyncSession,
    invite: Invite,
    used_by_telegram_id: int,
) -> Invite:
    """Invite ni ishlatilgan deb belgilash."""
    invite.is_used = True
    invite.used_by = used_by_telegram_id
    invite.used_at = datetime.now(timezone.utc)
    await session.flush()

    logger.info(
        f"🔗 Invite ishlatildi: {invite.code} "
        f"tomonidan telegram_id={used_by_telegram_id}"
    )

    return invite


async def delete_invite(
    session: AsyncSession,
    invite: Invite,
) -> None:
    """Invite ni o'chirish."""
    await session.delete(invite)
    await session.flush()

    logger.info(f"🗑 Invite o'chirildi: {invite.code}")
