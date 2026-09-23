"""Admin — Excel hisobotlar."""
from datetime import datetime

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsAdmin, text_key
from src.bot.keyboards.admin import export_keyboard
from src.database.models.user import User
from src.services.export_service import (
    generate_steps_report,
    generate_trucks_report,
)
from src.services.i18n_service import _


router = Router(name="admin_export")


# ==================== "Excel hisobot" menyusi ====================
@router.message(IsAdmin(), text_key("admin.menu_excel"))
async def show_export_menu(
    message: Message,
    user: User,
):
    """Excel hisobot menyusini ko'rsatish."""
    lang = user.language or "uz"

    text = (
        f"{_('admin.excel_title', language=lang)}\n\n"
        f"{_('admin.excel_choose', language=lang)}\n\n"
        f"📊 {_('admin.excel_trucks_all', language=lang)}\n"
        f"✅ {_('admin.excel_trucks_completed', language=lang)}\n"
        f"🔵 {_('admin.excel_trucks_in_progress', language=lang)}\n"
        f"📋 {_('admin.excel_steps_all', language=lang)}\n\n"
        f"{_('admin.excel_hint', language=lang)}"
    )

    await message.answer(
        text,
        reply_markup=export_keyboard(lang),
    )


# ==================== Trucklar hisoboti ====================
@router.callback_query(IsAdmin(), F.data == "export_trucks_all")
async def export_trucks_all(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Barcha trucklar hisoboti."""
    lang = user.language or "uz"
    await callback.answer(_("admin.excel_generating", language=lang))

    buf = await generate_trucks_report(session)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"trucks_{timestamp}.xlsx"

    await callback.message.answer_document(
        document=BufferedInputFile(buf.getvalue(), filename=filename),
        caption=(
            f"📊 <b>{_('admin.excel_trucks_all', language=lang)}</b>\n\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ),
    )


@router.callback_query(IsAdmin(), F.data == "export_trucks_completed")
async def export_trucks_completed(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Tayyor trucklar hisoboti."""
    lang = user.language or "uz"
    await callback.answer(_("admin.excel_generating", language=lang))

    buf = await generate_trucks_report(session, status_filter="completed")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"trucks_completed_{timestamp}.xlsx"

    await callback.message.answer_document(
        document=BufferedInputFile(buf.getvalue(), filename=filename),
        caption=(
            f"📊 <b>{_('admin.excel_trucks_completed', language=lang)}</b>\n\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ),
    )


@router.callback_query(IsAdmin(), F.data == "export_trucks_in_progress")
async def export_trucks_in_progress(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Jarayondagi trucklar hisoboti."""
    lang = user.language or "uz"
    await callback.answer(_("admin.excel_generating", language=lang))

    buf = await generate_trucks_report(session, status_filter="in_progress")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"trucks_in_progress_{timestamp}.xlsx"

    await callback.message.answer_document(
        document=BufferedInputFile(buf.getvalue(), filename=filename),
        caption=(
            f"📊 <b>{_('admin.excel_trucks_in_progress', language=lang)}</b>\n\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ),
    )


# ==================== Steplar hisoboti ====================
@router.callback_query(IsAdmin(), F.data == "export_steps_all")
async def export_steps_all(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Barcha steplar hisoboti."""
    lang = user.language or "uz"
    await callback.answer(_("admin.excel_generating", language=lang))

    buf = await generate_steps_report(session)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"steps_{timestamp}.xlsx"

    await callback.message.answer_document(
        document=BufferedInputFile(buf.getvalue(), filename=filename),
        caption=(
            f"📊 <b>{_('admin.excel_steps_all', language=lang)}</b>\n\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ),
    )
