"""QC FSM holatlari."""
from aiogram.fsm.state import State, StatesGroup


class RejectStepFSM(StatesGroup):
    """Stepni rad etish sababini kiritish."""
    reason = State()
