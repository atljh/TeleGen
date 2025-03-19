from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup

class MainMenu(StatesGroup):
    main = State()


main_dialog = Dialog(
    Window(
        state=MainMenu.main,
    )
)