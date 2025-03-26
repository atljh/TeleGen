from aiogram.fsm.state import State, StatesGroup

class GenerationMenu(StatesGroup):
    main = State()
    
    channel_main = State()
    create_flow = State()
    buffer = State()
    book_recall = State()
    message = State()