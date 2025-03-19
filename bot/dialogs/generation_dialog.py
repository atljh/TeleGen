from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup

class GenerationMenu(StatesGroup):
    main = State()

async def on_channel1(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Канал1")

async def on_channel2(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Канал2")

async def add_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Додати канал")


generation_dialog = Dialog(
    Window(
        Const("Оберiть канал\nабо додайте новий"),
        Row(
            Button(Const("Канал1"), id="channel1", on_click=on_channel1),
            Button(Const("Канал2"), id="channel2", on_click=on_channel2),
        ),
        Row(
            Button(Const("Додати канал"), id="add_channel", on_click=add_channel),
        ),
        state=GenerationMenu.main,
    )
)