"""Til tizimi (i18n) servisi."""
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.utils.logger import logger


# Tillar papkasi
LOCALES_DIR = Path(__file__).parent.parent.parent / "locales"

# Mavjud tillar
AVAILABLE_LANGUAGES = ["uz", "uz_cyrl", "ru"]

# Standart til
DEFAULT_LANGUAGE = "uz"


@lru_cache(maxsize=10)
def load_locale(language: str) -> dict[str, Any]:
    """Til faylini yuklash (cache bilan)."""
    if language not in AVAILABLE_LANGUAGES:
        logger.warning(
            f"⚠️ Til topilmadi: {language}, standart: {DEFAULT_LANGUAGE}"
        )
        language = DEFAULT_LANGUAGE

    locale_file = LOCALES_DIR / f"{language}.json"

    if not locale_file.exists():
        logger.error(f"❌ Til fayli topilmadi: {locale_file}")
        return {}

    try:
        with open(locale_file, encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"✅ Til yuklandi: {language}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON xato ({language}): {e}")
        return {}


def _(
    key: str,
    language: str = DEFAULT_LANGUAGE,
    **kwargs: Any,
) -> str:
    """Tarjima qilish.

    Args:
        key: Kalit (masalan, "start.welcome")
        language: Til kodi (uz, uz_cyrl, ru)
        **kwargs: Format uchun o'zgaruvchilar

    Returns:
        Tarjima qilingan matn
    """
    locale = load_locale(language)

    keys = key.split(".")
    value: Any = locale

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            if language != DEFAULT_LANGUAGE:
                return _(key, DEFAULT_LANGUAGE, **kwargs)
            logger.warning(f"⚠️ Tarjima topilmadi: {key}")
            return f"[{key}]"

    if isinstance(value, dict):
        logger.warning(f"⚠️ Kalit dict qaytardi: {key}")
        return f"[{key}]"

    if kwargs:
        try:
            return str(value).format(**kwargs)
        except KeyError as e:
            logger.error(f"❌ Format xato ({key}): {e}")
            return str(value)

    return str(value)


def get_step_name(step_number: int, language: str) -> str:
    """Step nomini tilga qarab olish."""
    return _(
        f"steps.{step_number}",
        language=language,
    )


def get_priority_name(priority: str, language: str) -> str:
    """Prioritet nomini tilga qarab olish."""
    # Enum → str
    priority_str = (
        priority.value if hasattr(priority, "value") else str(priority)
    )
    return _(
        f"priorities.{priority_str}",
        language=language,
    )


def get_status_name(status: str, language: str) -> str:
    """Holat nomini tilga qarab olish."""
    # Enum → str
    status_str = status.value if hasattr(status, "value") else str(status)
    return _(
        f"statuses.{status_str}",
        language=language,
    )


def get_role_name(role: str, language: str) -> str:
    """Rol nomini tilga qarab olish."""
    # Enum → str (UserRole.ADMIN → "admin")
    role_str = role.value if hasattr(role, "value") else str(role)
    return _(
        f"roles.{role_str}",
        language=language,
    )
