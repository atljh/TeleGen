from aiogram import Router, types, F
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram_dialog import DialogManager, StartMode

from dialogs.buffer_dialog import BufferMenu

router = Router()

@router.callback_query(F.data == "buffer")
async def handle_buffer(callback: types.CallbackQuery, dialog_manager: DialogManager):
    await callback.answer()
    await dialog_manager.start(state=BufferMenu.main, mode=StartMode.RESET_STACK)


def register_buffer(router: Router):
    router.callback_query.register(handle_buffer)
