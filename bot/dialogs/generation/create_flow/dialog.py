from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Column, Row, Next, Back
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.text import Const
from aiogram.enums import ParseMode

from .states import CreateFlowMenu
from .callbacks import(
    on_instagram,
    on_facebook,
    on_web,
    on_telegram,

    on_source_link_entered,
    on_existing_source_selected,
    on_add_new_source_type
)

def create_flow_dialog():
    return Dialog(
        Window(
            Const("Оберіть тип джерела з існуючих. Та послідовно додайте кожне з них по інструкції"),
            Column(
                Button(Const("Instagram"), id="instagram", on_click=on_instagram),
                Button(Const("Facebook"), id="facebook", on_click=on_facebook),
                Button(Const("Web"), id="web", on_click=on_web),
                Button(Const("Telegram"), id="telegram", on_click=on_telegram),
            ),
            Row(
                Next(Const("Далі"), id="next"),
            ),
            state=CreateFlowMenu.select_source,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Const("Відправьте лінк з обраного джерела за шаблоном"),
            Column(
                Button(Const("НАЗВА ДЖЕРЕЛА1"), id="source1"),
                Button(Const("НАЗВА ДЖЕРЕЛА2"), id="source2"),
                Button(Const("+ДОДАТИ НОВИЙ ТИП"), id="add_new_source_type"),
            ),
            Row(
                Back(Const("НАЗАД")),
            ),
            # Отдельно добавляем TextInput (не внутри Column)
            TextInput(
                id="source_link_input",
                on_success=on_source_link_entered,
            ),
            state=CreateFlowMenu.add_source_link,
            parse_mode=ParseMode.HTML,
        ),
    )