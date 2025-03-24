from aiogram import Router

from .start import register_handlers as register_start_handlers

router = Router()

def register_handlers():
    register_start_handlers(router)
    return router
