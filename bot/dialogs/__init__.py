from aiogram import Dispatcher

from .main_dialog import main_menu_dialog
from .generation_dialog import generation_dialog
from .settings_dialog import settings_dialog
from .support_dialog import support_dialog
from .buffer_dialog import buffer_dialog

def register_dialogs(dp: Dispatcher):
    dp.include_router(main_menu_dialog)
    dp.include_router(generation_dialog)
    dp.include_router(settings_dialog)
    dp.include_router(support_dialog)
    dp.include_router(buffer_dialog)
