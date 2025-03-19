from aiogram import types
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram_dialog import DialogManager, StartMode

from dialogs.generation_dialog import GenerationMenu


async def handle_generation(message: types.Message, dialog_manager: DialogManager):
    await message.answer("Ви обрали Генерацію 🚀")
    await dialog_manager.start(state=GenerationMenu.main, mode=StartMode.RESET_STACK)


def register_handlers(dp: Dispatcher):
    dp.message.register(handle_generation, lambda message: message.text == "Генерація")
