from aiogram_dialog import Window, Dialog
from aiogram.fsm.state import StatesGroup, State

class SettingsMenu(StatesGroup):
    main = State()
    channel_settings = State()
    channel_main_settings = State()
    confirm_delete = State()
    flow_settings = State()
    generation_frequency = State()
    character_limit = State()
    ad_block_settings = State()
    posts_in_flow = State()
    source_settings = State()
    # Добавьте другие состояния по мере необходимости