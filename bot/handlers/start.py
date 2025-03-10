from aiogram import types
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.filters import Command
from aiogram_dialog import DialogManager, StartMode

from dialogs.main_dialog import MainMenu

async def cmd_start(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=MainMenu.main, mode=StartMode.RESET_STACK)

def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))