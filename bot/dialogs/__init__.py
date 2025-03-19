from aiogram import Dispatcher

from .main_dialog import main_dialog
from .generation_dialog import generation_dialog

def register_dialogs(dp: Dispatcher):
    dp.include_router(main_dialog)
    dp.include_router(generation_dialog)