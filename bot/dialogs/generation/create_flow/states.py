from aiogram.fsm.state import State, StatesGroup

class CreateFlowMenu(StatesGroup):
    select_source = State()
    add_sources = State()
    add_source_link = State()
    select_frequency = State()
    select_words_limit = State()
    message_preview = State()
    title_highlight_confirm = State()
    ad_time_settings = State()

    flow_volume_settings = State()
    custom_volume_input = State()
    
    signature_settings = State()