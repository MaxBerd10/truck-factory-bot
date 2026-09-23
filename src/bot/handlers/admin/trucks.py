"""Admin — Trucklar boshqaruvi (FSM, i18n)."""
from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsAdmin, text_key
from src.bot.keyboards import (
    truck_cancel_keyboard,
    truck_confirm_keyboard,
    truck_detail_keyboard,
    truck_priority_keyboard,
    truck_skip_keyboard,
)
from src.bot.keyboards.truck import trucks_list_keyboard
from src.bot.states import AddTruckFSM
from src.database.models.user import User
from src.services.i18n_service import _, get_priority_name
from src.services.truck_service import (
    create_truck,
    delete_truck,
    get_truck_by_id,
    get_trucks_page,
)
from src.utils.logger import logger


router = Router(name="admin_trucks")


# ==================== "Trucklar" ====================
@router.message(IsAdmin(), text_key("admin.menu_trucks"))
async def show_trucks(
    message: Message,
    user: User,
    session: AsyncSession,
):
    """Trucklar ro'yxatini ko'rsatish."""
    await _send_trucks_list(message, user, session, page=0)


# ==================== Sahifalash ====================
@router.callback_query(IsAdmin(), F.data.startswith("trucks_page:"))
async def paginate_trucks(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Sahifani almashtirish."""
    page = int(callback.data.split(":")[1])
    await callback.answer()
    await _edit_trucks_list(callback, user, session, page)


# ==================== Bitta truckni ko'rish ====================
@router.callback_query(IsAdmin(), F.data.startswith("truck_view:"))
async def view_truck(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Bitta truckni ko'rish."""
    lang = user.language or "uz"
    truck_id = int(callback.data.split(":")[1])

    truck = await get_truck_by_id(session, truck_id)

    if not truck:
        await callback.answer(
            _("common.not_found", language=lang),
            show_alert=True,
        )
        return

    await callback.answer()
    await _show_truck_detail(callback.message, truck, lang, use_edit=True)


# ==================== O'chirishni tasdiqlash ====================
@router.callback_query(IsAdmin(), F.data.startswith("truck_delete:"))
async def delete_truck_confirm(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """O'chirishni tasdiqlash."""
    lang = user.language or "uz"
    truck_id = int(callback.data.split(":")[1])

    truck = await get_truck_by_id(session, truck_id)

    if not truck:
        await callback.answer(
            _("common.not_found", language=lang),
            show_alert=True,
        )
        return

    await callback.answer()

    await callback.message.edit_text(
        _(
            "admin.truck_delete_confirm",
            language=lang,
            truck=truck.serial_number,
        ),
        reply_markup=truck_cancel_keyboard(lang),
    )


# ==================== O'chirish ====================
@router.callback_query(IsAdmin(), F.data.startswith("truck_delete_ok:"))
async def delete_truck_handler(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    """Truckni o'chirish."""
    lang = user.language or "uz"
    truck_id = int(callback.data.split(":")[1])

    truck = await get_truck_by_id(session, truck_id)

    if not truck:
        await callback.answer(
            _("common.not_found", language=lang),
            show_alert=True,
        )
        return

    serial = truck.serial_number
    await delete_truck(session, truck)

    logger.info(f"🗑 Truck o'chirildi: {serial}")

    await callback.answer(
        _("admin.truck_deleted", language=lang),
        show_alert=True,
    )

    await _edit_trucks_list(callback, user, session, page=0)


# ==================== "Yangi truck" (FSM boshlash) ====================
@router.message(IsAdmin(), text_key("admin.menu_new_truck"))
async def start_add_truck(
    message: Message,
    state: FSMContext,
    user: User,
):
    """Yangi truck qo'shishni boshlash."""
    lang = user.language or "uz"
    await state.clear()
    await state.set_state(AddTruckFSM.serial_number)

    await message.answer(
        _("admin.truck_add_serial", language=lang),
        reply_markup=truck_cancel_keyboard(lang),
    )


# ==================== Inline "Yangi truck" tugmasi ====================
@router.callback_query(IsAdmin(), F.data == "truck_add")
async def start_add_truck_callback(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Inline tugmadan yangi truck qo'shish."""
    lang = user.language or "uz"
    await callback.answer()
    await state.clear()
    await state.set_state(AddTruckFSM.serial_number)

    await callback.message.edit_text(
        _("admin.truck_add_serial", language=lang),
        reply_markup=truck_cancel_keyboard(lang),
    )


# ==================== Serial raqam ====================
@router.message(AddTruckFSM.serial_number, F.text)
async def process_serial(
    message: Message,
    state: FSMContext,
    user: User,
    session: AsyncSession,
):
    """Serial raqamni qabul qilish."""
    lang = user.language or "uz"
    text = message.text.strip()

    if len(text) < 3:
        await message.answer(
            _("admin.truck_serial_too_short", language=lang),
            reply_markup=truck_cancel_keyboard(lang),
        )
        return

    # Takrorlanmasligini tekshirish
    from src.services.truck_service import get_truck_by_serial

    existing = await get_truck_by_serial(session, text)
    if existing:
        await message.answer(
            _("admin.truck_serial_exists", language=lang, serial=text),
            reply_markup=truck_cancel_keyboard(lang),
        )
        return

    await state.update_data(serial_number=text)
    await state.set_state(AddTruckFSM.model)

    await message.answer(
        _("admin.truck_add_model", language=lang),
        reply_markup=truck_skip_keyboard("model", lang),
    )


# ==================== Model ====================
@router.message(AddTruckFSM.model, F.text)
async def process_model(
    message: Message,
    state: FSMContext,
    user: User,
):
    """Modelni qabul qilish."""
    lang = user.language or "uz"
    await state.update_data(model=message.text.strip())
    await state.set_state(AddTruckFSM.customer)

    await message.answer(
        _("admin.truck_add_customer", language=lang),
        reply_markup=truck_skip_keyboard("customer", lang),
    )


# ==================== Modelni o'tkazib yuborish ====================
@router.callback_query(AddTruckFSM.model, F.data == "truck_skip_model")
async def skip_model(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Modelni o'tkazib yuborish."""
    lang = user.language or "uz"
    await callback.answer()
    await state.update_data(model=None)
    await state.set_state(AddTruckFSM.customer)

    await callback.message.edit_text(
        _("admin.truck_add_customer", language=lang),
        reply_markup=truck_skip_keyboard("customer", lang),
    )


# ==================== Customer ====================
@router.message(AddTruckFSM.customer, F.text)
async def process_customer(
    message: Message,
    state: FSMContext,
    user: User,
):
    """Buyurtmachini qabul qilish."""
    lang = user.language or "uz"
    await state.update_data(customer=message.text.strip())
    await state.set_state(AddTruckFSM.deadline)

    await message.answer(
        _("admin.truck_add_deadline", language=lang),
        reply_markup=truck_skip_keyboard("deadline", lang),
    )


# ==================== Customerni o'tkazib yuborish ====================
@router.callback_query(AddTruckFSM.customer, F.data == "truck_skip_customer")
async def skip_customer(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Buyurtmachini o'tkazib yuborish."""
    lang = user.language or "uz"
    await callback.answer()
    await state.update_data(customer=None)
    await state.set_state(AddTruckFSM.deadline)

    await callback.message.edit_text(
        _("admin.truck_add_deadline", language=lang),
        reply_markup=truck_skip_keyboard("deadline", lang),
    )


# ==================== Deadline ====================
@router.message(AddTruckFSM.deadline, F.text)
async def process_deadline(
    message: Message,
    state: FSMContext,
    user: User,
):
    """Muddatni qabul qilish."""
    lang = user.language or "uz"
    text = message.text.strip()

    try:
        deadline = datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        await message.answer(
            _("admin.truck_deadline_invalid", language=lang),
            reply_markup=truck_skip_keyboard("deadline", lang),
        )
        return

    await state.update_data(deadline=deadline.isoformat())
    await state.set_state(AddTruckFSM.priority)

    await message.answer(
        _("admin.truck_add_priority", language=lang),
        reply_markup=truck_priority_keyboard(lang),
    )


# ==================== Deadlineni o'tkazib yuborish ====================
@router.callback_query(AddTruckFSM.deadline, F.data == "truck_skip_deadline")
async def skip_deadline(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Muddatni o'tkazib yuborish."""
    lang = user.language or "uz"
    await callback.answer()
    await state.update_data(deadline=None)
    await state.set_state(AddTruckFSM.priority)

    await callback.message.edit_text(
        _("admin.truck_add_priority", language=lang),
        reply_markup=truck_priority_keyboard(lang),
    )


# ==================== Prioritet ====================
@router.callback_query(AddTruckFSM.priority, F.data.startswith("truck_priority:"))
async def process_priority(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Prioritetni qabul qilish."""
    lang = user.language or "uz"
    priority = callback.data.split(":")[1]
    await callback.answer()

    await state.update_data(priority=priority)
    await state.set_state(AddTruckFSM.confirm)

    await _show_truck_confirmation(callback.message, state, user, use_edit=True)


# ==================== Tasdiqlash ====================
@router.callback_query(AddTruckFSM.confirm, F.data == "truck_confirm")
async def confirm_add_truck(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    session: AsyncSession,
):
    """Truck yaratishni tasdiqlash."""
    lang = user.language or "uz"
    data = await state.get_data()
    await callback.answer()

    try:
        truck = await create_truck(
            session=session,
            serial_number=data["serial_number"],
            model=data.get("model"),
            customer=data.get("customer"),
            deadline=(
                datetime.fromisoformat(data["deadline"])
                if data.get("deadline")
                else None
            ),
            priority=data.get("priority", "normal"),
            created_by=user.telegram_id,
        )

        logger.info(
            f"➕ Truck yaratildi: {truck.serial_number} "
            f"(id={truck.id}) tomonidan {user.full_name}"
        )

        await state.clear()

        priority_name = get_priority_name(
            truck.priority, lang
        )

        text = (
            f"✅ <b>{_('admin.truck_created', language=lang)}</b>\n\n"
            f"🚛 <b>{truck.serial_number}</b>\n"
        )

        if truck.model:
            text += f"🏭 {truck.model}\n"
        if truck.customer:
            text += f"👤 {truck.customer}\n"
        if truck.deadline:
            text += f"📅 {truck.deadline.strftime('%Y-%m-%d')}\n"

        text += f"🎯 {priority_name}\n\n"
        text += f"<i>{_('admin.truck_steps_created', language=lang)}</i>"

        await callback.message.edit_text(
            text,
            reply_markup=truck_detail_keyboard(truck, back_page=0, language=lang),
        )

    except Exception as e:
        logger.exception(f"❌ Truck yaratishda xato: {e}")
        await state.clear()
        await callback.message.edit_text(
            _("common.error_generic", language=lang),
        )


# ==================== Bekor qilish ====================
@router.callback_query(F.data == "truck_cancel")
async def cancel_add_truck(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    session: AsyncSession,
):
    """Truck yaratishni bekor qilish."""
    lang = user.language or "uz"
    await callback.answer(_("common.cancel", language=lang))
    await state.clear()

    await _edit_trucks_list(callback, user, session, page=0)


# ==================== Qaytadan ====================
@router.callback_query(AddTruckFSM.confirm, F.data == "truck_restart")
async def restart_add_truck(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    """Boshidan boshlash."""
    lang = user.language or "uz"
    await callback.answer()
    await state.clear()
    await state.set_state(AddTruckFSM.serial_number)

    await callback.message.edit_text(
        _("admin.truck_add_serial", language=lang),
        reply_markup=truck_cancel_keyboard(lang),
    )


# ==================== Yordamchi funksiyalar ====================
async def _send_trucks_list(
    message: Message,
    user: User,
    session: AsyncSession,
    page: int = 0,
) -> None:
    """Trucklar ro'yxatini yuborish."""
    lang = user.language or "uz"
    trucks, total = await get_trucks_page(session, page=page, per_page=5)

    if not trucks:
        await message.answer(
            _("admin.trucks_empty", language=lang),
            reply_markup=trucks_list_keyboard([], page=0, total=0, language=lang),
        )
        return

    text = (
        f"{_('admin.trucks_title', language=lang)}\n\n"
        f"{_('admin.trucks_total', language=lang, count=total)}\n"
        f"{_('admin.trucks_page', language=lang, page=page + 1)}\n\n"
        f"{_('admin.trucks_choose', language=lang)}"
    )

    await message.answer(
        text,
        reply_markup=trucks_list_keyboard(
            trucks, page=page, per_page=5, total=total, language=lang
        ),
    )


async def _edit_trucks_list(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
    page: int = 0,
) -> None:
    """Trucklar ro'yxatini tahrirlash."""
    lang = user.language or "uz"
    trucks, total = await get_trucks_page(session, page=page, per_page=5)

    if not trucks:
        try:
            await callback.message.edit_text(
                _("admin.trucks_empty", language=lang),
                reply_markup=trucks_list_keyboard(
                    [], page=0, total=0, language=lang
                ),
            )
        except Exception:
            await callback.message.answer(
                _("admin.trucks_empty", language=lang),
                reply_markup=trucks_list_keyboard(
                    [], page=0, total=0, language=lang
                ),
            )
        return

    text = (
        f"{_('admin.trucks_title', language=lang)}\n\n"
        f"{_('admin.trucks_total', language=lang, count=total)}\n"
        f"{_('admin.trucks_page', language=lang, page=page + 1)}\n\n"
        f"{_('admin.trucks_choose', language=lang)}"
    )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=trucks_list_keyboard(
                trucks, page=page, per_page=5, total=total, language=lang
            ),
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=trucks_list_keyboard(
                trucks, page=page, per_page=5, total=total, language=lang
            ),
        )


async def _show_truck_detail(
    message: Message,
    truck,
    lang: str,
    use_edit: bool = True,
) -> None:
    """Truck tafsilotini ko'rsatish."""
    priority_name = get_priority_name(truck.priority, lang)

    status_map = {
        "in_progress": "statuses.in_progress",
        "completed": "statuses.completed",
        "cancelled": "statuses.cancelled",
    }
    status_name = _(
        status_map.get(truck.status, "statuses.in_progress"),
        language=lang,
    )

    text = (
        f"🚛 <b>{truck.serial_number}</b>\n\n"
        f"🏭 {truck.model or '—'}\n"
        f"👤 {truck.customer or '—'}\n"
    )

    if truck.deadline:
        text += f"📅 {truck.deadline.strftime('%Y-%m-%d')}\n"

    text += f"🎯 {priority_name}\n"
    text += f"📊 {status_name}\n"
    text += f"🔧 {truck.current_step}/6\n\n"

    if truck.created_at:
        text += f"📅 {truck.created_at.strftime('%Y-%m-%d %H:%M')}"

    keyboard = truck_detail_keyboard(truck, back_page=0, language=lang)

    if use_edit:
        try:
            await message.edit_text(text, reply_markup=keyboard)
        except Exception:
            await message.answer(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)


async def _show_truck_confirmation(
    message: Message,
    state: FSMContext,
    user: User,
    use_edit: bool = True,
) -> None:
    """Truck tasdiqlash oynasini ko'rsatish."""
    lang = user.language or "uz"
    data = await state.get_data()

    priority_name = get_priority_name(data.get("priority", "normal"), lang)

    text = (
        f"📋 <b>{_('common.confirm', language=lang)}</b>\n\n"
        f"🚛 <b>{data.get('serial_number')}</b>\n"
        f"🏭 {data.get('model') or '—'}\n"
        f"👤 {data.get('customer') or '—'}\n"
    )

    if data.get("deadline"):
        deadline = datetime.fromisoformat(data["deadline"])
        text += f"📅 {deadline.strftime('%Y-%m-%d')}\n"

    text += f"🎯 {priority_name}\n\n"
    text += f"<b>{_('admin.truck_confirm_question', language=lang)}</b>"

    keyboard = truck_confirm_keyboard(lang)

    if use_edit:
        try:
            await message.edit_text(text, reply_markup=keyboard)
        except Exception:
            await message.answer(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)
