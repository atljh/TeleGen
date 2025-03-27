from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Column, Row, Next, Back
from aiogram_dialog.widgets.text import Const
from aiogram.enums import ParseMode

from .states import CreateFlowMenu

def create_flow_dialog():
    return Dialog(
        Window(
            Const("Оберіть тип джерела з існуючих. Та послідовно додайте кожне з них по інструкції"),
            Column(
                Button(Const("Instagram"), id="instagram"),
                Button(Const("Facebook"), id="facebook"),
                Button(Const("Web"), id="web"),
                Button(Const("Telegram"), id="telegram"),
            ),
            Row(
                Next(Const("Далі"), id="next"),
            ),
            state=CreateFlowMenu.select_source,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Const("Message"),
            Row(
                Back(Const("Назад")),
            ),
            state=CreateFlowMenu.message_preview,
            parse_mode=ParseMode.HTML,
        )
    )