from aiogram.fsm.state import State, StatesGroup

class BufferMenu(StatesGroup):
    main = State()
    channel_main = State()
    edit_post = State()
    post_info = State()
    publish_confirm = State()