"""Ishchi — Ish yuborish (FSM)."""
from pathlib import Path
from uuid import uuid4

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsWorker
from src.bot.keyboards import (
    worker_after_submit_keyboard,
    worker_submit_cancel_keyboard,
    worker_submit_confirm_keyboard,
    worker_submit_skip_comment_keyboard,
    worker_tasks_keyboard,
)
from src.bot.states import SubmitWorkFSM
from src.config import settings
from src.database.models.user import User
from src.services.truck_step_service import (
    claim_step,
    get_step_with_truck,
    get_worker_tasks,
    submit_step,
)
from src.utils.constants import STEP_NAMES
from src.utils.logger import logger


router = Router(name="worker_submit")


# ==== "Ish yuborish" (reply tugma) ====
@router.message(IsWorker(), F.text == "📤 Ish yuborish")
async def submit_from_menu(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """Reply tugmadan ish yuborish."""
    tasks = await get_worker_tasks(session, user.id, user.step_number)

    if not tasks:
        await message.answer(
            "📤 <b>Ish yuborish</b>\n\n"
            "⚠️ Hozircha yuborish uchun ish yo'q.\n\n"
            "💡 <i>Yangi ish kelganda sizga xabar beramiz. "
            "Yoki \"📋 Vazifalarim\" ni tekshiring.</i>",
        )
        return

    if len(tasks) == 1:
        task = tasks[0]
        step_name = STEP_NAMES.get(
            task.step_number, f"Step {task.step_number}"
        )

        await message.answer(
            f"📤 <b>Ish yuborish</b>\n\n"
            f"🚛 Truck: <b>{task.truck.serial_number}</b>\n"
            f"🔧 Step: <b>{step_name}</b>\n\n"
            f"👇 Davom etish uchun quyidagi tugmani bosing:",
            reply_markup=worker_tasks_keyboard(tasks),
        )
        return

    await message.answer(
        f"📤 <b>Ish yuborish</b>\n\n"
        f"📊 Sizda <b>{len(tasks)}</b> ta ish bor.\n\n"
        f"👇 Qaysi ishni yubormoqchisiz?",
        reply_markup=worker_tasks_keyboard(tasks),
    )


# ==== "Ish yuborish" (inline callback) ====
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
        await callback.answer(
            "⚠️ Vazifa topilmadi\n\n"
            "Iltimos, \"📋 Vazifalarim\" ni yangilang.",
            show_alert=True,
        )
        return

    if step.step_number != user.step_number:
        await callback.answer(
            "⚠️ Bu sizning stepingiz emas\n\n"
            "Siz faqat o'z bo'limingizdagi ishlarni yuborishingiz mumkin.",
            show_alert=True,
        )
        return

    if step.status not in ["pending", "rejected"]:
        await callback.answer(
            "⚠️ Bu vazifa allaqachon yuborilgan\n\n"
            "Holatni \"📋 Vazifalarim\" da ko'rishingiz mumkin.",
            show_alert=True,
        )
        return

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
):
    """Rasmni qabul qilish."""
    await state.update_data(
        media_type="photo",
        media_file_id=message.photo[-1].file_id,
    )
    await state.set_state(SubmitWorkFSM.comment)

    await message.answer(
        "✅ <b>Rasm qabul qilindi.</b>\n\n"
        "📝 <b>Izoh qo'shing</b> (ixtiyoriy):\n\n"
        "<i>Masalan: Ichki qoplama tayyor, sifatli</i>",
        reply_markup=worker_submit_skip_comment_keyboard(),
    )


# ==== Media qabul qilish (video) ====
@router.message(SubmitWorkFSM.media, F.video)
async def process_video(
    message: Message,
    state: FSMContext,
):
    """Videoni qabul qilish."""
    await state.update_data(
        media_type="video",
        media_file_id=message.video.file_id,
    )
    await state.set_state(SubmitWorkFSM.comment)

    await message.answer(
        "✅ <b>Video qabul qilindi.</b>\n\n"
        "📝 <b>Izoh qo'shing</b> (ixtiyoriy):\n\n"
        "<i>Masalan: Ichki qoplama tayyor, sifatli</i>",
        reply_markup=worker_submit_skip_comment_keyboard(),
    )


# ==== Media qabul qilish (document) ====
@router.message(SubmitWorkFSM.media, F.document)
async def process_document(
    message: Message,
    state: FSMContext,
):
    """Hujjatni qabul qilish."""
    await state.update_data(
        media_type="document",
        media_file_id=message.document.file_id,
    )
    await state.set_state(SubmitWorkFSM.comment)

    await message.answer(
        "✅ <b>Hujjat qabul qilindi.</b>\n\n"
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
        "⚠️ <b>Faqat rasm, video yoki hujjat yuboring</b>\n\n"
        "📷 Rasm — kamera yoki galereyadan\n"
        "🎥 Video — 30 sekundgacha\n"
        "📄 Hujjat — PDF, Word va boshqalar\n\n"
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
            "⚠️ <b>Izoh juda uzun</b>\n\n"
            f"Sizning izohingiz: {len(text)} belgi\n"
            f"Maksimal: 1000 belgi\n\n"
            "Qisqartirib qaytadan yuboring:",
            reply_markup=worker_submit_skip_comment_keyboard(),
        )
        return

    await state.update_data(worker_comment=text)
    await state.set_state(SubmitWorkFSM.confirm)

    await _show_submit_confirmation(message, state, use_edit=False)


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

    media_type = data["media_type"]
    media_file_id = data["media_file_id"]
    media_local_path = None

    loading_msg = await callback.message.answer(
        "⏳ <b>Yuklanmoqda...</b>\n\n"
        "<i>Iltimos, kuting. Video katta bo'lsa, 30 sekundgacha olishi mumkin.</i>"
    )

    try:
        file = await bot.get_file(media_file_id)

        media_dir = Path(settings.MEDIA_ROOT)
        folder = media_dir / "trucks" / str(step.truck_id) / f"step_{step.step_number}"
        folder.mkdir(parents=True, exist_ok=True)

        ext_map = {"photo": ".jpg", "video": ".mp4", "document": ".bin"}
        ext = ext_map.get(media_type, ".bin")

        filename = f"{uuid4().hex}{ext}"
        local_path = folder / filename

        await bot.download_file(file.file_path, destination=str(local_path))
        media_local_path = str(local_path)

        logger.info(f"📁 Media saqlandi: {media_local_path}")

        try:
            await loading_msg.edit_text(
                "✅ <b>Media saqlandi!</b>\n\n"
                "<i>Endi QC ga yuborilmoqda...</i>"
            )
        except Exception:
            pass

    except Exception as e:
        logger.error(f"❌ Media saqlashda xato: {e}")
        try:
            await loading_msg.edit_text(
                "⚠️ <b>Media yuklashda xato!</b>\n\n"
                "<i>Lekin davom etamiz.</i>"
            )
        except Exception:
            pass

    await submit_step(
        session=session,
        step=step,
        worker_id=user.id,
        media_type=media_type,
        media_file_id=media_file_id,
        media_local_path=media_local_path,
        worker_comment=data.get("worker_comment"),
        bot=bot,
    )

    await state.clear()

    try:
        await loading_msg.delete()
    except Exception:
        pass

    step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")

    await callback.message.answer(
        f"✅ <b>Ish yuborildi!</b>\n\n"
        f"🚛 Truck: <b>{step.truck.serial_number}</b>\n"
        f"🔧 Step: <b>{step_name}</b>\n\n"
        f"📊 Holat: <b>🔍 QC tekshiruvida</b>\n\n"
        f"💡 <i>Sifat nazoratchisi tekshirib, tasdiqlaydi yoki rad etadi. "
        f"Natijani \"📋 Vazifalarim\" da ko'rasiz.</i>",
        reply_markup=worker_after_submit_keyboard(),
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
    use_edit: bool = True,
) -> None:
    """Tasdiqlash oynasini ko'rsatish."""
    data = await state.get_data()

    media_type = data.get("media_type", "photo")
    media_icon = {
        "photo": "📷 Rasm",
        "video": "🎥 Video",
        "document": "📄 Hujjat",
    }.get(media_type, "📎 Fayl")

    comment = data.get("worker_comment")
    comment_text = comment if comment else "<i>— yo'q —</i>"

    text = (
        f"📋 <b>Tasdiqlash</b>\n\n"
        f"📎 <b>Media:</b> {media_icon}\n"
        f"📝 <b>Izoh:</b> {comment_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Ishni yuborishni tasdiqlaysizmi?</b>\n\n"
        f"💡 <i>Yuborilgandan keyin QC tekshiradi. "
        f"Natijani \"📋 Vazifalarim\" da ko'rasiz.</i>"
    )

    if use_edit:
        try:
            await message.edit_text(
                text,
                reply_markup=worker_submit_confirm_keyboard(),
            )
        except Exception:
            await message.answer(
                text,
                reply_markup=worker_submit_confirm_keyboard(),
            )
    else:
        await message.answer(
            text,
            reply_markup=worker_submit_confirm_keyboard(),
        )
