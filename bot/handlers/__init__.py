from aiogram import Dispatcher
from aiogram import types

from .start import register_handlers as register_start_handlers
from .generation import handle_generation

def register_handlers(dp: Dispatcher):
    register_start_handlers(dp)
    handle_generation(dp)
    dp.message.register(handle_settings, lambda message: message.text == "Налаштування")
    dp.message.register(handle_help, lambda message: message.text == "Допомога")


async def handle_buffer(message: types.Message):
    await message.answer("Ви обрали Буфер 📥")

async def handle_settings(message: types.Message):
    await message.answer("Ви обрали Налаштування ⚙️")

async def handle_help(message: types.Message):
    await message.answer("Ви обрали Допомога ❓")
