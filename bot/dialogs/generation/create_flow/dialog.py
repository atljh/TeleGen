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

    on_once_a_day,
    on_once_a_12,
    on_once_an_hour,

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
            Const("Оберіть частоту генерацii"),
            Column(
                Button(Const("Раз на день"), id="once_a_day", on_click=on_once_a_day),
                Button(Const("Раз на 12 годин"), id="once_a_12", on_click=on_once_a_12),
                Button(Const("Раз на годину"), id="once_an_hour", on_click=on_once_an_hour),
            ),
            state=CreateFlowMenu.select_frequency,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Const("Оберіть обмеження по кiлькостi знакiв в постах"),
            Column(
                Button(Const("До 100"), id="instagram", on_click=on_instagram),
                Button(Const("До 300"), id="facebook", on_click=on_facebook),
                Button(Const("До 100"), id="web", on_click=on_web),
            ),
            state=CreateFlowMenu.select_words_limit,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Const("Відправьте лінк з обраного джерела за шаблоном"),
            Column(
                Button(Const("НАЗВА ДЖЕРЕЛА1"), id="source1", on_click=on_existing_source_selected),
                Button(Const("НАЗВА ДЖЕРЕЛА2"), id="source2", on_click=on_existing_source_selected),
                Button(Const("+ДОДАТИ НОВИЙ ТИП"), id="add_new_source_type", on_click=on_add_new_source_type),
            ),
            Row(
                Back(Const("НАЗАД")),
            ),
            TextInput(
                id="source_link_input",
                on_success=on_source_link_entered,
            ),
            state=CreateFlowMenu.add_source_link,
            parse_mode=ParseMode.MARKDOWN_V2,
        ),
    )