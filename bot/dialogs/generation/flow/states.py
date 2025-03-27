from aiogram.fsm.state import State, StatesGroup


class FlowMenu(StatesGroup):
    main = State()
    publish_now = State()
    schedule = State()
    edit = State()
    save_to_buffer = State()