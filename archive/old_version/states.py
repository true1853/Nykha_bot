from aiogram.fsm.state import StatesGroup, State

class DiaryStates(StatesGroup):
    waiting_for_entry = State()