"""Ishchi — Ish yuborish (FSM)."""
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsWorker
from src.bot.keyboards import (
    worker_submit_cancel_keyboard,
    worker_submit_confirm_keyboard,
    worker_submit_skip_comment_keyboard,
)
from src.bot.states import SubmitWorkFSM
from src.database.models.user import User
from src.services.truck_step_service import (
    claim_step,
    get_step_with_truck,
    submit_step,
)
from src.services.media_service import save_photo, save_video, save_document
from src.utils.constants import STEP_NAMES
from src.utils.logger import logger


router = Router(name="worker_submit")


# ==== "Ish yuborish" ====
@router.callback_query(IsWorker(), F.data.startswith("worker_submit:"))
async def start_submit(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    session: AsyncSession,
):
    """Ish yuborishni boshlash."""
    step_id = int(callback.data.split(":")[1])

    step = await get_step_with_truck(session, step_id)
    if not step:
        await callback.answer("❌ Vazifa topilmadi", show_alert=True)
        return

    # Ishchi o'z stepidami?
    if step.step_number != user.step_number:
        await callback.answer(
            "❌ Bu sizning stepingiz emas",
            show_alert=True,
        )
        return

    # Status tekshirish
    if step.status not in ["pending", "rejected"]:
        await callback.answer(
            "❌ Bu vazifa allaqachon yuborilgan",
            show_alert=True,
        )
        return

    # Stepni ishchiga biriktiramiz (claim)
    await claim_step(session, step, worker_id=user.id)

    await callback.answer()
    await state.clear()
    await state.update_data(step_id=step_id)
    await state.set_state(SubmitWorkFSM.media)

    step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")

    await callback.message.edit_text(
        f"📤 <b>Ish yuborish</b>\n\n"
        f"🚛 Truck: <b>{step.truck.serial_number}</b>\n"
        f"🔧 Step: <b>{step_name}</b>\n\n"
        f"📷 <b>Rasm yoki video yuboring:</b>\n\n"
        f"<i>Telegram orqali rasm/video yuboring.</i>",
        reply_markup=worker_submit_cancel_keyboard(),
    )


# ==== Media qabul qilish (rasm) ====
@router.message(SubmitWorkFSM.media, F.photo)
async def process_photo(
    message: Message,
    state: FSMContext,
    bot: Bot,
):
    """Rasmni qabul qilish."""
    data = await state.get_data()
    step_id = data["step_id"]

    # Rasmni saqlash
    # Avval step ni olish kerak (truck_id va step_number)
    # Hozircha faqat file_id ni saqlaymiz, keyin confirm da local_path ni saqlaymiz
    await state.update_data(
        media_type="photo",
        media_file_id=message.photo[-1].file_id,
    )
    await state.set_state(SubmitWorkFSM.comment)

    await message.answer(
        "✅ Rasm qabul qilindi.\n\n"
        "📝 <b>Izoh qo'shing</b> (ixtiyoriy):\n\n"
        "<i>Masalan: Ichki qoplama tayyor</i>",
        reply_markup=worker_submit_skip_comment_keyboard(),
    )


# ==== Media qabul qilish (video) ====
@router.message(SubmitWorkFSM.media, F.video)
async def process_video(
    message: Message,
    state: FSMContext,
    bot: Bot,
):
    """Videoni qabul qilish."""
    await state.update_data(
        media_type="video",
        media_file_id=message.video.file_id,
    )
    await state.set_state(SubmitWorkFSM.comment)

    await message.answer(
        "✅ Video qabul qilindi.\n\n"
        "📝 <b>Izoh qo'shing</b> (ixtiyoriy):\n\n"
        "<i>Masalan: Ichki qoplama tayyor</i>",
        reply_markup=worker_submit_skip_comment_keyboard(),
    )


# ==== Media qabul qilish (document) ====
@router.message(SubmitWorkFSM.media, F.document)
async def process_document(
    message: Message,
    state: FSMContext,
    bot: Bot,
):
    """Hujjatni qabul qilish."""
    await state.update_data(
        media_type="document",
        media_file_id=message.document.file_id,
    )
    await state.set_state(SubmitWorkFSM.comment)

    await message.answer(
        "✅ Hujjat qabul qilindi.\n\n"
        "📝 <b>Izoh qo'shing</b> (ixtiyoriy):",
        reply_markup=worker_submit_skip_comment_keyboard(),
    )


# ==== Noto'g'ri media ====
@router.message(SubmitWorkFSM.media)
async def invalid_media(
    message: Message,
    state: FSMContext,
):
    """Noto'g'ri media turi."""
    await message.answer(
        "❌ <b>Xato!</b>\n\n"
        "Iltimos, <b>rasm</b>, <b>video</b> yoki <b>hujjat</b> yuboring.\n\n"
        "Qaytadan urinib ko'ring:",
        reply_markup=worker_submit_cancel_keyboard(),
    )


# ==== Izohni o'tkazib yuborish ====
@router.callback_query(SubmitWorkFSM.comment, F.data == "worker_submit_skip_comment")
async def skip_comment(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Izohni o'tkazib yuborish."""
    await callback.answer()
    await state.update_data(worker_comment=None)
    await state.set_state(SubmitWorkFSM.confirm)

    await _show_submit_confirmation(callback.message, state)


# ==== Izoh qabul qilish ====
@router.message(SubmitWorkFSM.comment, F.text)
async def process_comment(
    message: Message,
    state: FSMContext,
):
    """Izohni qabul qilish."""
    text = message.text.strip()

    if len(text) > 1000:
        await message.answer(
            "❌ Izoh 1000 belgidan oshmasligi kerak.\n"
            "Qaytadan kiriting yoki o'tkazib yuboring:",
            reply_markup=worker_submit_skip_comment_keyboard(),
        )
        return

    await state.update_data(worker_comment=text)
    await state.set_state(SubmitWorkFSM.confirm)

    await _show_submit_confirmation(message, state)


# ==== Tasdiqlash ====
@router.callback_query(SubmitWorkFSM.confirm, F.data == "worker_submit_confirm")
async def confirm_submit(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    session: AsyncSession,
    bot: Bot,
):
    """Ishni yuborish."""
    data = await state.get_data()
    await callback.answer()

    step_id = data["step_id"]
    step = await get_step_with_truck(session, step_id)

    if not step:
        await callback.message.edit_text("❌ Xato: vazifa topilmadi")
        await state.clear()
        return

    # Media ni saqlash (hozir)
    media_type = data["media_type"]
    media_file_id = data["media_file_id"]
    media_local_path = None

    try:
        # Telegram dan yuklab olish
        file = await bot.get_file(media_file_id)

        # Papka
        from pathlib import Path
        from src.config import settings
        from uuid import uuid4

        media_dir = Path(settings.MEDIA_ROOT)
        folder = media_dir / "trucks" / str(step.truck_id) / f"step_{step.step_number}"
        folder.mkdir(parents=True, exist_ok=True)

        # Kengaytma
        ext_map = {"photo": ".jpg", "video": ".mp4", "document": ".bin"}
        ext = ext_map.get(media_type, ".bin")

        filename = f"{uuid4().hex}{ext}"
        local_path = folder / filename

        await bot.download_file(file.file_path, destination=str(local_path))
        media_local_path = str(local_path)

        logger.info(f"📁 Media saqlandi: {media_local_path}")

    except Exception as e:
        logger.error(f"❌ Media saqlashda xato: {e}")
        # Media saqlanmasa ham davom etamiz (file_id yetarli)

    # Step ni yuborish
    await submit_step(
        session=session,
        step=step,
        worker_id=user.id,
        media_type=media_type,
        media_file_id=media_file_id,
        media_local_path=media_local_path,
        worker_comment=data.get("worker_comment"),
    )

    await state.clear()

    step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")

    await callback.message.edit_text(
        f"✅ <b>Ish yuborildi!</b>\n\n"
        f"🚛 Truck: <b>{step.truck.serial_number}</b>\n"
        f"🔧 Step: <b>{step_name}</b>\n\n"
        f"📊 Holat: <b>🔍 QC tekshiruvida</b>\n\n"
        f"<i>Sifat nazoratchisi tekshirib, tasdiqlaydi yoki rad etadi.</i>"
    )


# ==== Qaytadan ====
@router.callback_query(SubmitWorkFSM.confirm, F.data == "worker_submit_restart")
async def restart_submit(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Boshidan boshlash."""
    await callback.answer()
    await state.set_state(SubmitWorkFSM.media)

    await callback.message.edit_text(
        "📷 <b>Rasm yoki video yuboring:</b>",
        reply_markup=worker_submit_cancel_keyboard(),
    )


# ==== Bekor qilish ====
@router.callback_query(F.data == "worker_submit_cancel")
async def cancel_submit(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Bekor qilish."""
    await callback.answer("❌ Bekor qilindi")
    await state.clear()

    await callback.message.edit_text(
        "❌ <b>Bekor qilindi.</b>\n\n"
        "Vazifalar ro'yxatiga qaytish uchun /start bosing."
    )


# ==== Yordamchi ====
async def _show_submit_confirmation(
    message: Message,
    state: FSMContext,
) -> None:
    """Tasdiqlash oynasini ko'rsatish."""
    data = await state.get_data()

    media_type = data.get("media_type", "photo")
    media_icon = {
        "photo": "📷 Rasm",
        "video": "🎥 Video",
        "document": "📄 Hujjat",
    }.get(media_type, "📎 Fayl")

    comment = data.get("worker_comment") or "—"

    text = (
        f"📋 <b>Tasdiqlash</b>\n\n"
        f"📎 Media: {media_icon}\n"
        f"📝 Izoh: {comment}\n\n"
        f"<b>Ishni yuborishni tasdiqlaysizmi?</b>\n\n"
        f"<i>Yuborilgandan keyin QC tekshiradi.</i>"
    )

    await message.edit_text(
        text,
        reply_markup=worker_submit_confirm_keyboard(),
    )
