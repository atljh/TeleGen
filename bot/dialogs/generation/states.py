from aiogram.fsm.state import State, StatesGroup

class GenerationMenu(StatesGroup):
    main = State()

class ChannelMenu:
    main = "channel_main"
    create_flow = "create_flow"
    buffer = "buffer"
    book_recall = "book_recall"
    message = "message"