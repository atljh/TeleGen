from aiogram.fsm.state import State, StatesGroup

class CreateFlowMenu(StatesGroup):
    select_source = State()
    add_sources = State()
    add_source_link = State()
    select_frequency = State()
    select_words_limit = State()
    message_preview = State()