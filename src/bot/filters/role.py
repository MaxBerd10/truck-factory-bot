"""Rol bo'yicha filterlar."""
from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from src.database.models.user import User


class IsRegistered(BaseFilter):
    """Faqat ro'yxatdan o'tgan va aktiv foydalanuvchilar uchun."""

    async def __call__(self, event: TelegramObject, **kwargs) -> bool:
        user: User | None = kwargs.get("user")
        return user is not None and user.is_active


class IsNotRegistered(BaseFilter):
    """Faqat ro'yxatdan o'tmagan foydalanuvchilar uchun."""

    async def __call__(self, event: TelegramObject, **kwargs) -> bool:
        user: User | None = kwargs.get("user")
        return user is None


class IsWorker(BaseFilter):
    """Faqat ishchilar uchun (worker, aktiv)."""

    async def __call__(self, event: TelegramObject, **kwargs) -> bool:
        user: User | None = kwargs.get("user")
        return user is not None and user.is_active and user.is_worker


class IsQC(BaseFilter):
    """Faqat sifat nazoratchilar uchun (QC, aktiv)."""

    async def __call__(self, event: TelegramObject, **kwargs) -> bool:
        user: User | None = kwargs.get("user")
        return user is not None and user.is_active and user.is_qc


class IsAdmin(BaseFilter):
    """Faqat adminlar uchun (aktiv)."""

    async def __call__(self, event: TelegramObject, **kwargs) -> bool:
        user: User | None = kwargs.get("user")
        return user is not None and user.is_active and user.is_admin
