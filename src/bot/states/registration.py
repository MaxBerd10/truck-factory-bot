"""Ro'yxatdan o'tish FSM."""
from aiogram.fsm.state import State, StatesGroup


class RegistrationFSM(StatesGroup):
    """Invite orqali ro'yxatdan o'tish."""
    full_name = State()
    phone = State()
    confirm = State()
