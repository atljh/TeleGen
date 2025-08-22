from aiogram.fsm.state import State, StatesGroup

class AddChannelMenu(StatesGroup):
    instructions = State()
    success = State()