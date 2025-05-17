from aiogram.fsm.state import State, StatesGroup

class BufferMenu(StatesGroup):
    main = State()
    channel_main = State()