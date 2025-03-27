from aiogram import Dispatcher
from aiogram_dialog import setup_dialogs

from .main import create_main_dialog
from .generation import (
    create_generation_dialog,
    create_add_channel_dialog,
    flow_dialog,
    create_flow_dialog,
)
from .buffer import create_buffer_dialog
from .settings import create_settings_dialog
from .support import create_support_dialog

def register_dialogs(dp: Dispatcher):
    main_dialog = create_main_dialog()
    generation_dialog = create_generation_dialog()
    add_channel_dialog = create_add_channel_dialog()
    d_flow_dialog = flow_dialog()
    d_create_flow_dialog = create_flow_dialog()
    buffer_dialog = create_buffer_dialog()
    settings_dialog = create_settings_dialog()
    support_dialog = create_support_dialog()
    
    dp.include_router(main_dialog)
    dp.include_router(generation_dialog)
    dp.include_router(add_channel_dialog)
    dp.include_router(d_flow_dialog)
    dp.include_router(d_create_flow_dialog)
    dp.include_router(buffer_dialog)
    dp.include_router(settings_dialog)
    dp.include_router(support_dialog)