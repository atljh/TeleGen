from aiogram.fsm.state import State, StatesGroup

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.kbd import Button, Row

class MainMenu(StatesGroup):
    main = State()


main_menu_dialog = Dialog(
    Window(
        Const("Вітаємо у PROPOST! Виберіть опцію:"),
        Row(
            Button(Const("Генерація"), id="generate"),
            Button(Const("Буфер"), id="buffer"),
        ),
        Row(
            Button(Const("Налаштування"), id="settings"),
            Button(Const("Допомога"), id="help"),
        ),
        state=MainMenu.main,
    )
)