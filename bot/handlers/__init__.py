from aiogram import Router

from .start import register_handlers as register_start_handlers
from .generation import register_generation
from .settings import register_settings
from .support import register_support
from .buffer import register_buffer

router = Router()

def register_handlers():
    register_start_handlers(router)
    register_generation(router)
    register_settings(router)
    register_support(router)
    register_buffer(router)
    
    return router
