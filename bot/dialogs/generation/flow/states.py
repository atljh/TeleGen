from aiogram.fsm.state import State, StatesGroup


class FlowMenu(StatesGroup):
    main = State()
    posts_list = State()
    edit_post = State()
    publish_now = State()
    schedule = State()
    save_to_buffer = State()