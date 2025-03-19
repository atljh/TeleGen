from aiogram import Dispatcher
from aiogram import types

from .start import register_handlers as register_start_handlers
from .generation import register_generation
from .settings import register_settings
from .support import register_support
from .buffer import register_buffer

def register_handlers(dp: Dispatcher):
    register_start_handlers(dp)
    register_generation(dp)
    register_settings(dp)
    register_support(dp)
    register_buffer(dp)

