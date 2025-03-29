# handlers/__init__.py
from aiogram import Router
from aiogram.dispatcher.dispatcher import Dispatcher 
from .start import register_handlers as register_start_handlers

router = Router()

def register_handlers(dp: Dispatcher):
    register_start_handlers(dp)