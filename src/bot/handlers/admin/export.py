"""Admin — Excel hisobotlar."""
from datetime import datetime

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsAdmin
from src.services.export_service import (
    generate_steps_report,
    generate_trucks_report,
)


router = Router(name="admin_export")


# ==== Trucklar hisoboti ====
@router.callback_query(IsAdmin(), F.data == "export_trucks_all")
async def export_trucks_all(
    callback: CallbackQuery,
    session: AsyncSession,
):
    """Barcha trucklar hisoboti."""
    await callback.answer("📊 Hisobot tayyorlanmoqda...")

    buf = await generate_trucks_report(session)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"trucks_{timestamp}.xlsx"

    await callback.message.answer_document(
        document=BufferedInputFile(
            buf.getvalue(),
            filename=filename,
        ),
        caption=(
            "📊 <b>Trucklar hisoboti</b>\n\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            "📋 Barcha trucklar"
        ),
    )


@router.callback_query(IsAdmin(), F.data == "export_trucks_completed")
async def export_trucks_completed(
    callback: CallbackQuery,
    session: AsyncSession,
):
    """Tayyor trucklar hisoboti."""
    await callback.answer("📊 Hisobot tayyorlanmoqda...")

    buf = await generate_trucks_report(session, status_filter="completed")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"trucks_completed_{timestamp}.xlsx"

    await callback.message.answer_document(
        document=BufferedInputFile(
            buf.getvalue(),
            filename=filename,
        ),
        caption=(
            "📊 <b>Trucklar hisoboti</b>\n\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            "✅ Faqat tayyor trucklar"
        ),
    )


@router.callback_query(IsAdmin(), F.data == "export_trucks_in_progress")
async def export_trucks_in_progress(
    callback: CallbackQuery,
    session: AsyncSession,
):
    """Jarayondagi trucklar hisoboti."""
    await callback.answer("📊 Hisobot tayyorlanmoqda...")

    buf = await generate_trucks_report(session, status_filter="in_progress")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"trucks_in_progress_{timestamp}.xlsx"

    await callback.message.answer_document(
        document=BufferedInputFile(
            buf.getvalue(),
            filename=filename,
        ),
        caption=(
            "📊 <b>Trucklar hisoboti</b>\n\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            "🔵 Jarayondagi trucklar"
        ),
    )


# ==== Steplar hisoboti ====
@router.callback_query(IsAdmin(), F.data == "export_steps_all")
async def export_steps_all(
    callback: CallbackQuery,
    session: AsyncSession,
):
    """Barcha steplar hisoboti."""
    await callback.answer("📊 Hisobot tayyorlanmoqda...")

    buf = await generate_steps_report(session)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"steps_{timestamp}.xlsx"

    await callback.message.answer_document(
        document=BufferedInputFile(
            buf.getvalue(),
            filename=filename,
        ),
        caption=(
            "📊 <b>Steplar hisoboti</b>\n\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            "📋 Barcha steplar"
        ),
    )
