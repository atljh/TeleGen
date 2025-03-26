from aiogram.fsm.state import State, StatesGroup

class AddChannelMenu(StatesGroup):
    enter_channel_id = State()
    instructions = State()
    check_permissions = State()
    success = State()