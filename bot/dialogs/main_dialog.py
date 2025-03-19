from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup

class MainMenu(StatesGroup):
    main = State()

async def on_click(callback: CallbackQuery, button: Button, manager: DialogManager):
    # await callback.message.answer("Ви натиснули кнопку! 🎉")
    ...

main_dialog = Dialog(
    Window(
        Const("Привіт! Це головне меню. 🚀"),
        Button(Const("Натисни мене"), id="btn_click", on_click=on_click),
        state=MainMenu.main,
    )
)