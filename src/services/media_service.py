"""Media fayllarni saqlash servisi."""
import os
from pathlib import Path
from uuid import uuid4

from aiogram import Bot
from aiogram.types import Message, PhotoSize, Video

from src.config import settings
from src.utils.logger import logger


# Media papkasi
MEDIA_DIR = Path(settings.MEDIA_ROOT)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


async def save_photo(
    bot: Bot,
    message: Message,
    truck_id: int,
    step_number: int,
) -> tuple[str, str]:
    """Rasmni saqlash.

    Returns:
        (file_id, local_path)
    """
    # Eng katta o'lchamdagi rasmni olamiz
    photo: PhotoSize = message.photo[-1]

    # Faylni yuklab olamiz
    file = await bot.get_file(photo.file_id)

    # Papka: media/trucks/{truck_id}/step_{step_number}/
    folder = MEDIA_DIR / "trucks" / str(truck_id) / f"step_{step_number}"
    folder.mkdir(parents=True, exist_ok=True)

    # Fayl nomi
    filename = f"{uuid4().hex}.jpg"
    local_path = folder / filename

    # Yuklab olamiz
    await bot.download_file(file.file_path, destination=str(local_path))

    logger.info(
        f"📷 Rasm saqlandi: {local_path} "
        f"(truck_id={truck_id}, step={step_number})"
    )

    return photo.file_id, str(local_path)


async def save_video(
    bot: Bot,
    message: Message,
    truck_id: int,
    step_number: int,
) -> tuple[str, str]:
    """Videoni saqlash.

    Returns:
        (file_id, local_path)
    """
    video: Video = message.video

    file = await bot.get_file(video.file_id)

    folder = MEDIA_DIR / "trucks" / str(truck_id) / f"step_{step_number}"
    folder.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}.mp4"
    local_path = folder / filename

    await bot.download_file(file.file_path, destination=str(local_path))

    logger.info(
        f"🎥 Video saqlandi: {local_path} "
        f"(truck_id={truck_id}, step={step_number})"
    )

    return video.file_id, str(local_path)


async def save_document(
    bot: Bot,
    message: Message,
    truck_id: int,
    step_number: int,
) -> tuple[str, str]:
    """Hujjatni saqlash."""
    document = message.document

    file = await bot.get_file(document.file_id)

    folder = MEDIA_DIR / "trucks" / str(truck_id) / f"step_{step_number}"
    folder.mkdir(parents=True, exist_ok=True)

    # Kengaytma
    ext = Path(document.file_name or "file").suffix or ".bin"
    filename = f"{uuid4().hex}{ext}"
    local_path = folder / filename

    await bot.download_file(file.file_path, destination=str(local_path))

    logger.info(
        f"📄 Hujjat saqlandi: {local_path} "
        f"(truck_id={truck_id}, step={step_number})"
    )

    return document.file_id, str(local_path)
