from aiogram import types
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram_dialog import DialogManager, StartMode

from dialogs.settings_dialog import SettingsMenu


async def handle_settings(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=SettingsMenu.main, mode=StartMode.RESET_STACK)


def register_settings(dp: Dispatcher):
    dp.message.register(handle_settings, lambda message: message.text == "Налаштування")
