from aiogram.fsm.state import State, StatesGroup

class CreateFlowMenu(StatesGroup):
    select_source = State()
    add_sources = State()
    message_preview = State()