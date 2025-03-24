from aiogram import Dispatcher

from .main import create_main_dialog
from .generation import create_generation_dialog

def register_dialogs(dp: Dispatcher):
    dp.include_router(create_main_dialog())
    dp.include_router(create_generation_dialog())