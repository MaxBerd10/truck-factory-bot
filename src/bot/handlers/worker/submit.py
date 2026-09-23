"""Ishchi — Ish yuborish (FSM)."""
from pathlib import Path
from uuid import uuid4

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsWorker, text_key
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
from src.services.i18n_service import _, get_step_name
from src.services.truck_step_service import (
    claim_step,
    get_step_with_truck,
    get_worker_tasks,
    submit_step,
)
from src.utils.logger import logger


router = Router(name="worker_submit")


# ==================== "Ish yuborish" (reply tugma) ====================
@router.message(IsWorker(), text_key("worker.menu_submit"))
async def submit_from_menu(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """Reply tugmadan ish yuborish."""
    lang = user.language or "uz"

    tasks = await get_worker_tasks(session, user.id, user.step_number)

    if not tasks:
        await message.answer(
            _("worker.no_tasks_to_submit", language=lang),
        )
        return

    if len(tasks) == 1:
        task = tasks[0]
        step_name = get_step_name(task.step_number, lang)

        await message.answer(
            _(
                "worker.one_task_prompt",
                language=lang,
                truck=task.truck.serial_number,
                step=step_name,
            ),
            reply_markup=worker_tasks_keyboard(tasks, lang),
        )
        return

    await message.answer(
        _("worker.multiple_tasks_prompt", language=lang, count=len(tasks)),
        reply_markup=worker_tasks_keyboard(tasks, lang),
    )


# ==================== "Ish yuborish" (inline callback) ====================
@router.callback_query(IsWorker(), F.data.startswith("worker_submit:"))
async def start_submit(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    session: AsyncSession,
):
    """Ish yuborishni boshlash."""
    lang = user.language or "uz"
    step_id = int(callback.data.split(":")[1])

    step = await get_step_with_truck(session, step_id)

    if not step:
        await callback.answer(
            _("common.not_found", language=lang),
            show_alert=True,
        )
        return

    if step.step_number != user.step_number:
        await callback.answer(
            _("worker.wrong_step", language=lang),
            show_alert=True,
        )
        return

    if step.status not in ["pending", "rejected"]:
        await callback.answer(
            _("worker.already_submitted", language=lang),
            show_alert=True,
        )
        return

    await claim_step(session, step, worker_id=user.id)

    await callback.answer()
    await state.clear()
    await state.update_data(step_id=step_id)
    await state.set_state(SubmitWorkFSM.media)

    step_name = get_step_name(step.step_number, lang)

    await callback.message.edit_text(
        _("worker.submit_title", language=lang)
        + f"\n\n🚛 <b>{step.truck.serial_number}</b>\n"
        + f"🔧 <b>{step_name}</b>\n\n"
        + _("worker.submit_media_prompt", language=lang),
        reply_markup=worker_submit_cancel_keyboard(lang),
    )


# ==================== Media qabul qilish (rasm) ====================
@router.message(SubmitWorkFSM.media, F.photo)
async def process_photo(
    message: Message,
    state: FSMContext,
    user: User,
):
    """Rasmni qabul qilish."""
    lang = user.language or "uz"

    await state.update_data(
        media_type="photo",
        media_file_id=message.photo[-1].file_id,
    )
    await state.set_state(SubmitWorkFSM.comment)

    await message.answer(
        _("worker.submit_photo_received", language=lang),
        reply_markup=worker_submit_skip_comment_keyboard(lang),
    )


# ==================== Media qabul qilish (video) ====================
@router.message(SubmitWorkFSM.media, F.video)
async def process_video(
    message: Message,
    state: FSMContext,
    user: User,
):
    """Videoni qabul qilish."""
    lang = user.language or "uz"

    await state.update_data(
        media_type="video",
        media_file_id=message.video.file_id,
    )
    await state.set_state(SubmitWorkFSM.comment)

    await message.answer(
        _("worker.submit_video_received", language=lang),
        reply_markup=worker_submit_skip_comment_keyboard(lang),
    )


# ==================== Media qabul qilish (document) ====================
@router.message(SubmitWorkFSM.media, F.document)
async def process_document(
    message: Message,
    state: FSMContext,
    user: User,
):
    """Hujjatni qabul qilish."""
    lang = user.language or "uz"

    await state.update_data(
        media_type="document",
        media_file_id=message.document.file_id,
    )
    await state.set_state(SubmitWorkFSM.comment)

    await message.answer(
        _("worker.submit_doc_received", language=lang),
        reply_markup=worker_submit_skip_comment_keyboard(lang),
    )


# ==================== Noto'g'ri media ====================
@router.message(SubmitWorkFSM.media)
async def invalid_media(
    message: Message,
    state: FSMContext,
    user: User,
):
    """Noto'g'ri media turi."""
    lang = user.language or "uz"

    await message.answer(
        _("worker.submit_invalid_media", language=lang),
        reply_markup=worker_submit_cancel_keyboard(lang),
    )


# ==================== Izohni o'tkazib yuborish ====================
@router.callback_query(
    SubmitWorkFSM.comment,
    F.data == "worker_submit_skip_comment",
)
async def skip_comment(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Izohni o'tkazib yuborish."""
    await callback.answer()
    await state.update_data(worker_comment=None)
    await state.set_state(SubmitWorkFSM.confirm)

    await _show_submit_confirmation(callback.message, state, user)


# ==================== Izoh qabul qilish ====================
@router.message(SubmitWorkFSM.comment, F.text)
async def process_comment(
    message: Message,
    state: FSMContext,
    user: User,
):
    """Izohni qabul qilish."""
    lang = user.language or "uz"
    text = message.text.strip()

    if len(text) > 1000:
        await message.answer(
            _("worker.submit_comment_too_long", language=lang, len=len(text)),
            reply_markup=worker_submit_skip_comment_keyboard(lang),
        )
        return

    await state.update_data(worker_comment=text)
    await state.set_state(SubmitWorkFSM.confirm)

    await _show_submit_confirmation(message, state, user, use_edit=False)


# ==================== Tasdiqlash ====================
@router.callback_query(
    SubmitWorkFSM.confirm,
    F.data == "worker_submit_confirm",
)
async def confirm_submit(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    session: AsyncSession,
    bot: Bot,
):
    """Ishni yuborish."""
    lang = user.language or "uz"
    data = await state.get_data()
    await callback.answer()

    step_id = data["step_id"]
    step = await get_step_with_truck(session, step_id)

    if not step:
        await callback.message.edit_text(
            _("common.not_found", language=lang)
        )
        await state.clear()
        return

    media_type = data["media_type"]
    media_file_id = data["media_file_id"]
    media_local_path = None

    loading_msg = await callback.message.answer(
        _("worker.submit_loading", language=lang)
    )

    try:
        file = await bot.get_file(media_file_id)

        media_dir = Path(settings.MEDIA_ROOT)
        folder = (
            media_dir
            / "trucks"
            / str(step.truck_id)
            / f"step_{step.step_number}"
        )
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
                _("worker.submit_saved", language=lang)
            )
        except Exception:
            pass

    except Exception as e:
        logger.error(f"❌ Media saqlashda xato: {e}")
        try:
            await loading_msg.edit_text(
                _("worker.submit_error_save", language=lang)
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

    step_name = get_step_name(step.step_number, lang)

    await callback.message.answer(
        _(
            "worker.submit_success",
            language=lang,
            truck=step.truck.serial_number,
            step=step_name,
        ),
        reply_markup=worker_after_submit_keyboard(lang),
    )


# ==================== Qaytadan ====================
@router.callback_query(
    SubmitWorkFSM.confirm,
    F.data == "worker_submit_restart",
)
async def restart_submit(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Boshidan boshlash."""
    lang = user.language or "uz"
    await callback.answer()
    await state.set_state(SubmitWorkFSM.media)

    await callback.message.edit_text(
        _("worker.submit_media_prompt", language=lang),
        reply_markup=worker_submit_cancel_keyboard(lang),
    )


# ==================== Bekor qilish ====================
@router.callback_query(F.data == "worker_submit_cancel")
async def cancel_submit(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Bekor qilish."""
    lang = user.language or "uz"
    await callback.answer(_("common.cancel", language=lang))
    await state.clear()

    await callback.message.edit_text(
        _("common.cancelled", language=lang)
    )


# ==================== Yordamchi ====================
async def _show_submit_confirmation(
    message: Message,
    state: FSMContext,
    user: User,
    use_edit: bool = True,
) -> None:
    """Tasdiqlash oynasini ko'rsatish."""
    lang = user.language or "uz"
    data = await state.get_data()

    media_type = data.get("media_type", "photo")
    media_icon = {
        "photo": "📷 Rasm",
        "video": "🎥 Video",
        "document": "📄 Hujjat",
    }.get(media_type, "📎 Fayl")

    comment = data.get("worker_comment")
    comment_text = comment if comment else _(
        "worker.submit_confirm_no_comment", language=lang
    )

    text = (
        f"{_('worker.submit_confirm_title', language=lang)}\n\n"
        f"{_('worker.submit_confirm_media', language=lang, media=media_icon)}\n"
        f"{_('worker.submit_confirm_comment', language=lang, comment=comment_text)}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>{_('worker.submit_confirm_question', language=lang)}</b>\n\n"
        f"💡 <i>{_('worker.submit_confirm_hint', language=lang)}</i>"
    )

    if use_edit:
        try:
            await message.edit_text(
                text,
                reply_markup=worker_submit_confirm_keyboard(lang),
            )
        except Exception:
            await message.answer(
                text,
                reply_markup=worker_submit_confirm_keyboard(lang),
            )
    else:
        await message.answer(
            text,
            reply_markup=worker_submit_confirm_keyboard(lang),
        )
