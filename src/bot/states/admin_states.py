"""Admin FSM holatlari."""
from aiogram.fsm.state import State, StatesGroup


class AddUserFSM(StatesGroup):
    """Yangi user qo'shish bosqichlari."""
    telegram_id = State()
    full_name = State()
    phone = State()
    role = State()
    step_number = State()
    confirm = State()
