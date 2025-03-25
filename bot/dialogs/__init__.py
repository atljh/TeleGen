from aiogram import Dispatcher

from .main import create_main_dialog
from .generation import (
    create_generation_dialog,
    create_add_channel_dialog
)
from .buffer import create_buffer_dialog
from .settings import create_settings_dialog
from .support import create_support_dialog


def register_dialogs(dp: Dispatcher):
    dp.include_router(create_main_dialog())

    dp.include_router(create_generation_dialog())
    dp.include_router(create_add_channel_dialog())

    dp.include_router(create_buffer_dialog())
    dp.include_router(create_settings_dialog())
    dp.include_router(create_support_dialog())
