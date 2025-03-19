from aiogram import types
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram_dialog import DialogManager, StartMode

from dialogs.buffer_dialog import BufferMenu


async def handle_buffer(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=BufferMenu.main, mode=StartMode.RESET_STACK)


def register_buffer(dp: Dispatcher):
    dp.message.register(handle_buffer, lambda message: message.text == "Буфер")
