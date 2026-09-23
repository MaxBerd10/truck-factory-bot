"""Admin — Trucklar boshqaruvi."""
from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import IsAdmin
from src.bot.keyboards import (
    truck_confirm_keyboard,
    truck_detail_keyboard,
    truck_priority_keyboard,
    truck_skip_keyboard,
    trucks_list_keyboard,
)
from src.bot.states import AddTruckFSM
from src.database.models.truck import Truck
from src.database.models.user import User
from src.services.truck_service import (
    create_truck,
    delete_truck,
    get_truck_by_id,
    get_trucks_page,
)
from src.utils.constants import (
    PRIORITY_NAMES,
    SOURCE_NAMES,
    STATUS_NAMES,
    STEP_NAMES,
)


router = Router(name="admin_trucks")


# ==== Trucklar bo'limi ====
@router.message(IsAdmin(), F.text == "🚛 Trucklar")
async def show_trucks_menu(
    message: Message,
    session: AsyncSession,
):
    """Trucklar ro'yxatini ko'rsatish."""
    await _send_trucks_list(message, session, page=0)


# ==== Sahifalash ====
@router.callback_query(IsAdmin(), F.data.startswith("trucks_page:"))
async def paginate_trucks(
    callback: CallbackQuery,
    session: AsyncSession,
):
    """Sahifani almashtirish."""
    page = int(callback.data.split(":")[1])
    await callback.answer()
    await _edit_trucks_list(callback, session, page)


# ==== Bitta truckni ko'rish ====
@router.callback_query(IsAdmin(), F.data.startswith("truck_view:"))
async def view_truck(
    callback: CallbackQuery,
    session: AsyncSession,
):
    """Bitta truckni ko'rish."""
    truck_id = int(callback.data.split(":")[1])

    truck = await get_truck_by_id(session, truck_id)
    if not truck:
        await callback.answer("❌ Truck topilmadi", show_alert=True)
        return

    await callback.answer()
    await _show_truck_detail(callback.message, truck)


# ==== O'chirish ====
@router.callback_query(IsAdmin(), F.data.startswith("truck_delete:"))
async def confirm_delete_truck(
    callback: CallbackQuery,
    session: AsyncSession,
):
    """Truckni o'chirish."""
    truck_id = int(callback.data.split(":")[1])

    truck = await get_truck_by_id(session, truck_id)
    if not truck:
        await callback.answer("❌ Truck topilmadi", show_alert=True)
        return

    serial = truck.serial_number
    await delete_truck(session, truck)
    await callback.answer(f"🗑 {serial} o'chirildi", show_alert=True)

    # Ro'yxatga qaytish
    await _edit_trucks_list(callback, session, page=0)


# ==== Yangi truck qo'shish (FSM) ====
@router.callback_query(IsAdmin(), F.data == "truck_add")
async def start_add_truck(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Yangi truck qo'shishni boshlash."""
    await callback.answer()
    await state.clear()
    await state.set_state(AddTruckFSM.serial_number)

    await callback.message.edit_text(
        "➕ <b>Yangi truck qo'shish</b>\n\n"
        "1️⃣ <b>Serial raqamni kiriting:</b>\n\n"
        "<i>Masalan: TR-2026-001</i>",
        reply_markup=None,
    )


# ==== 1. Serial number ====
@router.message(AddTruckFSM.serial_number, F.text)
async def process_serial_number(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    """Serial raqamni qabul qilish."""
    text = message.text.strip()

    if len(text) < 3 or len(text) > 64:
        await message.answer(
            "❌ <b>Xato!</b>\n\n"
            "Serial raqam 3 dan 64 belgigacha bo'lishi kerak.\n"
            "Qaytadan kiriting:",
        )
        return

    # Unikal ekanligini tekshirish
    from src.services.truck_service import get_truck_by_serial
    existing = await get_truck_by_serial(session, text)
    if existing:
        await message.answer(
            f"⚠️ <b>Bu serial raqam allaqachon mavjud!</b>\n\n"
            f"🚛 {existing.serial_number}\n\n"
            f"Boshqa serial kiriting:",
        )
        return

    await state.update_data(serial_number=text)
    await state.set_state(AddTruckFSM.model)

    await message.answer(
        f"✅ Serial: <b>{text}</b>\n\n"
        f"2️⃣ <b>Modelni kiriting</b> (ixtiyoriy):\n\n"
        f"<i>Masalan: KamAZ 5490</i>",
        reply_markup=truck_skip_keyboard("model"),
    )


# ==== 2. Model (ixtiyoriy) ====
@router.callback_query(AddTruckFSM.model, F.data == "truck_skip_model")
async def skip_model(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Modelni o'tkazib yuborish."""
    await callback.answer()
    await state.update_data(model=None)
    await state.set_state(AddTruckFSM.customer)

    await callback.message.edit_text(
        "✅ Model: <i>o'tkazib yuborildi</i>\n\n"
        "3️⃣ <b>Buyurtmachini kiriting</b> (ixtiyoriy):\n\n"
        "<i>Masalan: OOO 'Toshkent Logistics'</i>",
        reply_markup=truck_skip_keyboard("customer"),
    )


@router.message(AddTruckFSM.model, F.text)
async def process_model(
    message: Message,
    state: FSMContext,
):
    """Modelni qabul qilish."""
    text = message.text.strip()

    if len(text) > 128:
        await message.answer(
            "❌ Model 128 belgidan oshmasligi kerak.\n"
            "Qaytadan kiriting yoki o'tkazib yuboring:",
            reply_markup=truck_skip_keyboard("model"),
        )
        return

    await state.update_data(model=text)
    await state.set_state(AddTruckFSM.customer)

    await message.answer(
        f"✅ Model: <b>{text}</b>\n\n"
        f"3️⃣ <b>Buyurtmachini kiriting</b> (ixtiyoriy):\n\n"
        f"<i>Masalan: OOO 'Toshkent Logistics'</i>",
        reply_markup=truck_skip_keyboard("customer"),
    )


# ==== 3. Customer (ixtiyoriy) ====
@router.callback_query(AddTruckFSM.customer, F.data == "truck_skip_customer")
async def skip_customer(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Buyurtmachini o'tkazib yuborish."""
    await callback.answer()
    await state.update_data(customer=None)
    await state.set_state(AddTruckFSM.deadline)

    await callback.message.edit_text(
        "✅ Buyurtmachi: <i>o'tkazib yuborildi</i>\n\n"
        "4️⃣ <b>Muddatni kiriting</b> (ixtiyoriy):\n\n"
        "<i>Format: YYYY-MM-DD (masalan: 2026-10-15)</i>",
        reply_markup=truck_skip_keyboard("deadline"),
    )


@router.message(AddTruckFSM.customer, F.text)
async def process_customer(
    message: Message,
    state: FSMContext,
):
    """Buyurtmachini qabul qilish."""
    text = message.text.strip()

    if len(text) > 255:
        await message.answer(
            "❌ Buyurtmachi nomi 255 belgidan oshmasligi kerak.\n"
            "Qaytadan kiriting yoki o'tkazib yuboring:",
            reply_markup=truck_skip_keyboard("customer"),
        )
        return

    await state.update_data(customer=text)
    await state.set_state(AddTruckFSM.deadline)

    await message.answer(
        f"✅ Buyurtmachi: <b>{text}</b>\n\n"
        f"4️⃣ <b>Muddatni kiriting</b> (ixtiyoriy):\n\n"
        f"<i>Format: YYYY-MM-DD (masalan: 2026-10-15)</i>",
        reply_markup=truck_skip_keyboard("deadline"),
    )


# ==== 4. Deadline (ixtiyoriy) ====
@router.callback_query(AddTruckFSM.deadline, F.data == "truck_skip_deadline")
async def skip_deadline(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Muddatni o'tkazib yuborish."""
    await callback.answer()
    await state.update_data(deadline=None)
    await state.set_state(AddTruckFSM.priority)

    await callback.message.edit_text(
        "✅ Muddat: <i>o'tkazib yuborildi</i>\n\n"
        "5️⃣ <b>Prioritetni tanlang:</b>",
        reply_markup=truck_priority_keyboard(),
    )


@router.message(AddTruckFSM.deadline, F.text)
async def process_deadline(
    message: Message,
    state: FSMContext,
):
    """Muddatni qabul qilish."""
    text = message.text.strip()

    try:
        deadline = datetime.strptime(text, "%Y-%m-%d").replace(
            tzinfo=UTC
        )
    except ValueError:
        await message.answer(
            "❌ <b>Xato format!</b>\n\n"
            "Muddat YYYY-MM-DD formatida bo'lishi kerak.\n"
            "<i>Masalan: 2026-10-15</i>\n\n"
            "Qaytadan kiriting yoki o'tkazib yuboring:",
            reply_markup=truck_skip_keyboard("deadline"),
        )
        return

    await state.update_data(deadline=deadline.isoformat())
    await state.set_state(AddTruckFSM.priority)

    await message.answer(
        f"✅ Muddat: <b>{deadline.strftime('%Y-%m-%d')}</b>\n\n"
        f"5️⃣ <b>Prioritetni tanlang:</b>",
        reply_markup=truck_priority_keyboard(),
    )


# ==== 5. Priority ====
@router.callback_query(AddTruckFSM.priority, F.data.startswith("truck_priority:"))
async def process_priority(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Prioritetni tanlash."""
    priority = callback.data.split(":")[1]
    await callback.answer()

    await state.update_data(priority=priority)
    await state.set_state(AddTruckFSM.confirm)

    await _show_truck_confirmation(callback.message, state)


# ==== 6. Tasdiqlash ====
@router.callback_query(AddTruckFSM.confirm, F.data == "truck_confirm")
async def confirm_add_truck(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User,
):
    """Truckni DB ga saqlash."""
    data = await state.get_data()
    await callback.answer()

    # Deadline ni datetime ga o'girish
    deadline = None
    if data.get("deadline"):
        deadline = datetime.fromisoformat(data["deadline"])

    try:
        truck = await create_truck(
            session=session,
            serial_number=data["serial_number"],
            model=data.get("model"),
            customer=data.get("customer"),
            deadline=deadline,
            priority=data.get("priority", "normal"),
            created_by=user.telegram_id,
            source="admin",
        )
    except ValueError as e:
        await callback.message.edit_text(
            f"❌ <b>Xato:</b> {e}"
        )
        await state.clear()
        return

    await state.clear()

    role_name = PRIORITY_NAMES.get(truck.priority, truck.priority)

    text = (
        f"✅ <b>Truck yaratildi!</b>\n\n"
        f"🚛 Serial: <b>{truck.serial_number}</b>\n"
    )

    if truck.model:
        text += f"🏭 Model: {truck.model}\n"
    if truck.customer:
        text += f"👤 Buyurtmachi: {truck.customer}\n"
    if truck.deadline:
        text += f"📅 Muddat: {truck.deadline.strftime('%Y-%m-%d')}\n"

    text += f"🎯 Prioritet: {role_name}\n\n"
    text += "<i>6 ta step avtomatik yaratildi.</i>"

    await callback.message.edit_text(
        text,
        reply_markup=truck_detail_keyboard(truck),
    )


# ==== Qaytadan ====
@router.callback_query(AddTruckFSM.confirm, F.data == "truck_restart")
async def restart_add_truck(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Boshidan boshlash."""
    await callback.answer()
    await state.clear()
    await state.set_state(AddTruckFSM.serial_number)

    await callback.message.edit_text(
        "➕ <b>Yangi truck qo'shish</b>\n\n"
        "1️⃣ <b>Serial raqamni kiriting:</b>\n\n"
        "<i>Masalan: TR-2026-001</i>"
    )


# ==== Bekor qilish ====
@router.callback_query(F.data == "truck_cancel")
async def cancel_add_truck(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    """Bekor qilish."""
    await callback.answer("❌ Bekor qilindi")
    await state.clear()

    await _edit_trucks_list(callback, session, page=0)


# ==== Yordamchi funksiyalar ====
async def _send_trucks_list(
    message: Message,
    session: AsyncSession,
    page: int = 0,
) -> None:
    """Yangi xabar bilan trucklar ro'yxatini yuborish."""
    trucks, total = await get_trucks_page(session, page, per_page=10)

    if total == 0:
        await message.answer(
            "🚛 <b>Trucklar</b>\n\n"
            "Hozircha trucklar yo'q.\n\n"
            "➕ Yangi qo'shish uchun quyidagi tugmani bosing.",
            reply_markup=trucks_list_keyboard([], page=0, total=0),
        )
        return

    text = (
        f"🚛 <b>Trucklar</b>\n\n"
        f"Jami: <b>{total}</b> ta\n"
        f"Sahifa: <b>{page + 1}</b>\n\n"
        f"Batafsil ko'rish uchun truckni tanlang:"
    )

    await message.answer(
        text,
        reply_markup=trucks_list_keyboard(
            trucks, page=page, per_page=10, total=total
        ),
    )


async def _edit_trucks_list(
    callback: CallbackQuery,
    session: AsyncSession,
    page: int = 0,
) -> None:
    """Mavjud xabarni tahrirlab, trucklar ro'yxatini yangilash."""
    trucks, total = await get_trucks_page(session, page, per_page=10)

    if total == 0:
        await callback.message.edit_text(
            "🚛 <b>Trucklar</b>\n\n"
            "Hozircha trucklar yo'q.",
            reply_markup=trucks_list_keyboard([], page=0, total=0),
        )
        return

    text = (
        f"🚛 <b>Trucklar</b>\n\n"
        f"Jami: <b>{total}</b> ta\n"
        f"Sahifa: <b>{page + 1}</b>\n\n"
        f"Batafsil ko'rish uchun truckni tanlang:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=trucks_list_keyboard(
            trucks, page=page, per_page=10, total=total
        ),
    )


async def _show_truck_detail(message: Message, truck: Truck) -> None:
    """Truck tafsilotini ko'rsatish."""
    priority_name = PRIORITY_NAMES.get(truck.priority, truck.priority)
    status_name = STATUS_NAMES.get(
        "completed" if truck.is_completed else "in_review",
        "🔄 Jarayonda",
    )
    source_name = SOURCE_NAMES.get(truck.source, truck.source)

    text = (
        f"🚛 <b>Truck: {truck.serial_number}</b>\n\n"
    )

    if truck.model:
        text += f"🏭 Model: {truck.model}\n"
    if truck.customer:
        text += f"👤 Buyurtmachi: {truck.customer}\n"
    if truck.deadline:
        text += f"📅 Muddat: {truck.deadline.strftime('%Y-%m-%d')}\n"

    text += f"🎯 Prioritet: {priority_name}\n"
    text += f"📊 Holat: {status_name}\n"
    text += f"📍 Hozirgi step: <b>{truck.current_step}/6</b>\n"
    text += f"📋 Manba: {source_name}\n\n"

    # Steplar ro'yxati
    text += "<b>Steplar:</b>\n"
    for step in truck.steps:
        step_name = STEP_NAMES.get(step.step_number, f"Step {step.step_number}")

        # Status icon
        status_icon = {
            "pending": "⏳",
            "in_review": "🔍",
            "approved": "✅",
            "rejected": "❌",
        }.get(step.status, "❓")

        text += f"  {status_icon} {step_name}\n"

    await message.edit_text(
        text,
        reply_markup=truck_detail_keyboard(truck),
    )


async def _show_truck_confirmation(
    message: Message,
    state: FSMContext,
) -> None:
    """Tasdiqlash oynasini ko'rsatish."""
    data = await state.get_data()

    priority_name = PRIORITY_NAMES.get(
        data.get("priority", "normal"), "Oddiy"
    )

    deadline_text = "—"
    if data.get("deadline"):
        deadline = datetime.fromisoformat(data["deadline"])
        deadline_text = deadline.strftime("%Y-%m-%d")

    text = (
        f"📋 <b>Tasdiqlash</b>\n\n"
        f"🚛 Serial: <b>{data['serial_number']}</b>\n"
        f"🏭 Model: {data.get('model') or '—'}\n"
        f"👤 Buyurtmachi: {data.get('customer') or '—'}\n"
        f"📅 Muddat: {deadline_text}\n"
        f"🎯 Prioritet: {priority_name}\n\n"
        f"<b>Truck yaratilsinmi?</b>\n\n"
        f"<i>6 ta step avtomatik yaratiladi.</i>"
    )

    await message.edit_text(
        text,
        reply_markup=truck_confirm_keyboard(),
    )
