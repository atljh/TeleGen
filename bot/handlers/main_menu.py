from aiogram import types
from aiogram import Router, F
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram_dialog import DialogManager, StartMode

from dialogs.settings.states import SettingsMenu
from dialogs.buffer.states import BufferMenu
from dialogs.generation.states import GenerationMenu
from dialogs.support.states import SupportMenu


router = Router()

@router.message(F.text == "⚙️ Налаштування")
async def handle_settings(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=SettingsMenu.main, mode=StartMode.RESET_STACK)

@router.message(F.text == "✨ Генерацiя")
async def handle_generation(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=GenerationMenu.main, mode=StartMode.RESET_STACK)

@router.message(F.text == "📂 Буфер")
async def handle_buffer(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=BufferMenu.preview, mode=StartMode.RESET_STACK)

@router.message(F.text == "❓ Допомога")
async def handle_support(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=SupportMenu.main, mode=StartMode.RESET_STACK)




