from aiogram import types
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram_dialog import DialogManager, StartMode
from dialogs.support_dialog import SupportMenu


async def handle_support(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=SupportMenu.main, mode=StartMode.RESET_STACK)


def register_support(dp: Dispatcher):
    dp.message.register(handle_support, lambda message: message.text == "Допомога")
