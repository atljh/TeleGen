from aiogram import Dispatcher

from .main_dialog import main_dialog

def register_dialogs(dp: Dispatcher):
    dp.include_router(main_dialog)