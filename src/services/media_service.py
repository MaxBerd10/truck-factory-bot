"""Media fayllarni saqlash servisi."""
from pathlib import Path
from uuid import uuid4

from aiogram import Bot
from aiogram.types import Message

from src.config import settings


async def save_photo(
    message: Message,
    bot: Bot,
    subfolder: str = "",
) -> tuple[str, str]:
    """Rasmni saqlash.

    Returns:
        tuple: (file_id, local_path)
    """
    if not message.photo:
        raise ValueError("Rasm topilmadi")

    photo = message.photo[-1]
    file_id = photo.file_id

    file = await bot.get_file(file_id)
    if not file.file_path:
        raise ValueError("File path topilmadi")

    filename = f"{uuid4().hex}.jpg"

    media_dir = Path(settings.MEDIA_ROOT) / subfolder
    media_dir.mkdir(parents=True, exist_ok=True)
    local_path = media_dir / filename

    await bot.download_file(file.file_path, destination=str(local_path))

    return file_id, str(local_path)


async def save_video(
    message: Message,
    bot: Bot,
    subfolder: str = "",
) -> tuple[str, str]:
    """Videoni saqlash.

    Returns:
        tuple: (file_id, local_path)
    """
    if not message.video:
        raise ValueError("Video topilmadi")

    video = message.video
    file_id = video.file_id

    file = await bot.get_file(file_id)
    if not file.file_path:
        raise ValueError("File path topilmadi")

    filename = f"{uuid4().hex}.mp4"

    media_dir = Path(settings.MEDIA_ROOT) / subfolder
    media_dir.mkdir(parents=True, exist_ok=True)
    local_path = media_dir / filename

    await bot.download_file(file.file_path, destination=str(local_path))

    return file_id, str(local_path)


async def save_document(
    message: Message,
    bot: Bot,
    subfolder: str = "",
) -> tuple[str, str]:
    """Hujjatni saqlash.

    Returns:
        tuple: (file_id, local_path)
    """
    if not message.document:
        raise ValueError("Hujjat topilmadi")

    document = message.document
    file_id = document.file_id

    file = await bot.get_file(file_id)
    if not file.file_path:
        raise ValueError("File path topilmadi")

    # Kengaytma
    ext = ".bin"
    if document.file_name:
        ext = Path(document.file_name).suffix or ".bin"

    filename = f"{uuid4().hex}{ext}"

    media_dir = Path(settings.MEDIA_ROOT) / subfolder
    media_dir.mkdir(parents=True, exist_ok=True)
    local_path = media_dir / filename

    await bot.download_file(file.file_path, destination=str(local_path))

    return file_id, str(local_path)
