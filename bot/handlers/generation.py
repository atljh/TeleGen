from aiogram import Router, types, F
from aiogram_dialog import DialogManager, StartMode

from dialogs.generation_dialog import GenerationMenu

router = Router()

@router.message(F.text == "Генерація")  # Используем F.text вместо lambda
async def handle_generation(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=GenerationMenu.main, mode=StartMode.RESET_STACK)

def register_generation(router: Router):
    router.message.register(handle_generation)
