"""Matn kaliti bo'yicha filter (i18n uchun)."""
from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import Message

from src.services.i18n_service import _


class TextKeyFilter(BaseFilter):
    """Matn kaliti bo'yicha filter.

    Foydalanuvchining tiliga qarab, barcha tillardagi tarjimalarni tekshiradi.

    Misol:
        @router.message(IsWorker(), text_key("worker.menu_tasks"))
        async def show_tasks(message: Message):
            ...
    """

    def __init__(self, key: str) -> None:
        self.key = key
        # Barcha tillardagi tarjimalarni oldindan yuklash
        self.translations: set[str] = set()
        for lang in ["uz", "uz_cyrl", "ru"]:
            translation = _(key, language=lang)
            if translation and not translation.startswith("["):
                self.translations.add(translation)

    async def __call__(
        self,
        message: Message,
        **kwargs: Any,
    ) -> bool:
        """Matn kalitga mos keladimi?"""
        if not message.text:
            return False
        return message.text in self.translations


def text_key(key: str) -> TextKeyFilter:
    """Matn kaliti bo'yicha filter yaratish.

    Misol:
        @router.message(text_key("worker.menu_tasks"))
        async def show_tasks(message: Message):
            ...
    """
    return TextKeyFilter(key)

