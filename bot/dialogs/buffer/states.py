from aiogram.fsm.state import State, StatesGroup

class BufferMenu(StatesGroup):
    preview = State()
    edit_text = State()
    edit_media = State()
    set_schedule = State()
    confirm_publish = State()