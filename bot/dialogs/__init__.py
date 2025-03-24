from aiogram import Dispatcher

from .main import create_main_dialog
from .generation import create_generation_dialog
from .buffer import create_buffer_dialog

def register_dialogs(dp: Dispatcher):
    dp.include_router(create_main_dialog())
    dp.include_router(create_generation_dialog())
    dp.include_router(create_buffer_dialog())