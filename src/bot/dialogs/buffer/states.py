from aiogram.fsm.state import State, StatesGroup


class BufferMenu(StatesGroup):
    main = State()
    channel_main = State()
    post_info = State()
    edit_post = State()
    edit_schedule = State()
    cancel_publish_confirm = State()
    publish_confirm = State()
