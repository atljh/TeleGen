from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup

class SupportMenu(StatesGroup):
    main = State()

async def instructions(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Інструкції")

async def sms_support(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Зв'язок із підтримкою")


support_dialog = Dialog(
    Window(
        Const("Допомога"),
        Row(
            Button(Const("Інструкції"), id="instructions", on_click=instructions),
            Button(Const("Зв'язок із підтримкою"), id="sms_support", on_click=sms_support),
        ),
        state=SupportMenu.main,
    )
)