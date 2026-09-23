"""Rol filterlari (IsAdmin, IsWorker, IsQC va h.k.)."""
from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from src.database.models.user import User


class IsRegistered(BaseFilter):
    """Faqat ro'yxatdan o'tgan foydalanuvchilar."""

    async def __call__(
        self,
        event: Message | CallbackQuery,
        user: User | None = None,
        **kwargs: Any,
    ) -> bool:
        return user is not None


class IsNotRegistered(BaseFilter):
    """Faqat ro'yxatdan o'tmagan foydalanuvchilar."""

    async def __call__(
        self,
        event: Message | CallbackQuery,
        user: User | None = None,
        **kwargs: Any,
    ) -> bool:
        return user is None


class IsWorker(BaseFilter):
    """Faqat ishchilar (worker)."""

    async def __call__(
        self,
        event: Message | CallbackQuery,
        user: User | None = None,
        **kwargs: Any,
    ) -> bool:
        return user is not None and user.role == "worker"


class IsQC(BaseFilter):
    """Faqat sifat nazoratchilari (qc)."""

    async def __call__(
        self,
        event: Message | CallbackQuery,
        user: User | None = None,
        **kwargs: Any,
    ) -> bool:
        return user is not None and user.role == "qc"


class IsAdmin(BaseFilter):
    """Faqat administratorlar."""

    async def __call__(
        self,
        event: Message | CallbackQuery,
        user: User | None = None,
        **kwargs: Any,
    ) -> bool:
        return user is not None and user.role == "admin"
