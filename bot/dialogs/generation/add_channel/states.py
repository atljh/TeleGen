from aiogram.fsm.state import State, StatesGroup

class AddChannelMenu(StatesGroup):
    instructions = State()
    check_permissions = State()
    enter_channel_id = State()