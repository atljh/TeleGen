from aiogram.fsm.state import State, StatesGroup


class FlowMenu(StatesGroup):
    posts_list = State()
    post_info = State()
    edit_post = State()
    schedule = State()
    save_to_buffer = State()
    select_date = State()
    select_type = State()
    input_time = State()
    select_time = State()
    confirm_schedule = State()
    publish_confirm = State()
