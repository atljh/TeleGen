from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Format

class MainMenu(StatesGroup):
    main = State()


main_menu_dialog = Dialog(
    Window(
        Format(
            "*Вітаємо у PROPOST\!* 🎉\n\n"
            "Оберіть опцію з меню нижче:\n"
            "👇👇👇"
        ),
        Row(
            Button(Const("✨ Генерація"), id="generate"),
            Button(Const("📂 Буфер"), id="buffer"),
        ),
        Row(
            Button(Const("⚙️ Налаштування"), id="settings"),
            Button(Const("❓ Допомога"), id="help"),
        ),
        state=MainMenu.main,
        parse_mode=ParseMode.MARKDOWN_V2,
    )
)