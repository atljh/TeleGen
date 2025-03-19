from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup

class SettingsMenu(StatesGroup):
    main = State()

async def on_channel1(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Канал1")

async def on_channel2(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Канал2")

async def pay_subscription(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Оплата пiдписки")


settings_dialog = Dialog(
    Window(
        Const("Налаштування\n\nОберiть канал"),
        Row(
            Button(Const("Канал1"), id="channel1", on_click=on_channel1),
            Button(Const("Канал2"), id="channel2", on_click=on_channel2),
        ),
        Row(
            Button(Const("Оплата пiдписки"), id="pay_subscription", on_click=pay_subscription),
        ),
        state=SettingsMenu.main,
    )
)