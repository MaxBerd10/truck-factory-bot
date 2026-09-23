"""Admin FSM holatlari."""
from aiogram.fsm.state import State, StatesGroup


class CreateInviteFSM(StatesGroup):
    """Invite link yaratish bosqichlari."""

    role = State()
    step_number = State()
    expires_in = State()
    max_uses = State()
    confirm = State()


class AddTruckFSM(StatesGroup):
    """Yangi truck qo'shish bosqichlari."""

    serial_number = State()
    model = State()
    customer = State()
    deadline = State()
    priority = State()
    confirm = State()


class AddUserFSM(StatesGroup):
    """Yangi foydalanuvchi qo'shish bosqichlari."""

    telegram_id = State()
    full_name = State()
    role = State()
    step_number = State()
    phone = State()
    confirm = State()
