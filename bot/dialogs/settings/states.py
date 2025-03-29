from aiogram.fsm.state import State, StatesGroup

class SettingsMenu(StatesGroup):
    main = State()
    channel_settings = State()
    channel_main_settings = State()