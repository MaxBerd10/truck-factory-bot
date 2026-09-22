"""Worker FSM."""
from aiogram.fsm.state import State, StatesGroup


class SubmitWorkFSM(StatesGroup):
    """Ish yuborish bosqichlari."""
    media = State()       # Rasm/video kutish
    comment = State()     # Izoh kutish
    confirm = State()     # Tasdiqlash
