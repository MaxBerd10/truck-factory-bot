"""User middleware — foydalanuvchini DB dan yuklab, data['user'] ga qo'yadi."""
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types import User as TgUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.user import User
from src.utils.logger import logger


class UserMiddleware(BaseMiddleware):
    """Foydalanuvchini DB dan yuklaydi.

    Agar topilmasa — data['user'] = None.
    Bu middleware IsRegistered/IsNotRegistered filterlar bilan ishlaydi.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")

        if tg_user is None:
            data["user"] = None
            return await handler(event, data)

        session: AsyncSession = data["session"]

        stmt = select(User).where(User.telegram_id == tg_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        data["user"] = user

        if user:
            logger.debug(
                f"👤 User topildi: {user.full_name} "
                f"(role={user.role}, step={user.step_number}, active={user.is_active})"
            )
        else:
            logger.debug(f"👤 User topilmadi: telegram_id={tg_user.id}")

        return await handler(event, data)
