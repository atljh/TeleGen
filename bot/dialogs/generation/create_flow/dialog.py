from aiogram import F
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Column, Row, Next, Back, Select
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput
from aiogram.enums import ParseMode

from utils.buttons import go_back_to_main
from dialogs.settings.flow_settings.callbacks import open_flow_settings
from .states import CreateFlowMenu
from .getters import (
    ad_time_getter,
    flow_volume_getter,
    signature_getter,
    flow_confirmation_getter
)
from .callbacks import(
    to_channel,

    on_instagram,
    on_facebook,
    on_web,
    on_telegram,

    on_once_a_day,
    on_once_a_12,
    on_once_an_hour,

    on_to_100,
    on_to_300,
    on_to_1000,

    on_source_link_entered,
    on_existing_source_selected,
    on_add_new_source_type,
    
    confirm_title_highlight,
    reject_title_highlight,
    
    handle_time_input,
    reset_ad_time,
    
    on_volume_selected,
    open_custom_volume_input,
    handle_custom_volume_input,
    
    handle_signature_input,
    skip_signature
)
from dialogs.generation.callbacks import on_create_flow

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
                Button(Const("🔙 Назад"), id="to_channel", on_click=to_channel),
                Next(Const("🔜 Далі"), id="next"),
            ),
            Row(
                Button(Const("В головне меню"), id="go_back_to_main", on_click=go_back_to_main)
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
            Row(
                Back(Const("🔙 Назад")),
            ),
            Row(
                Button(Const("В головне меню"), id="go_back_to_main", on_click=go_back_to_main)
            ),
            state=CreateFlowMenu.select_frequency,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Const("Оберіть обмеження по кiлькостi знакiв в постах"),
            Column(
                Button(Const("До 100"), id="to_100", on_click=on_to_100),
                Button(Const("До 300"), id="to_300", on_click=on_to_300),
                Button(Const("До 1000"), id="to_1000", on_click=on_to_1000),
            ),
            Row(
                Back(Const("🔙 Назад")),
            ),
            Row(
                Button(Const("В головне меню"), id="go_back_to_main", on_click=go_back_to_main)
            ),
            state=CreateFlowMenu.select_words_limit,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Const("✏️ <b>Чи потрібно виділяти заголовок?</b>\n\n"),
            Column(
                Button(
                    Const("✅ Так"),
                    id="highlight_yes",
                    on_click=confirm_title_highlight
                ),
                Button(
                    Const("❌ Ні"),
                    id="highlight_no",
                    on_click=reject_title_highlight
                ),
            ),
            Row(
                Back(Const("◀️ Назад")),
            ),
            state=CreateFlowMenu.title_highlight_confirm,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Format("⏰ <b>Налаштування рекламного топу</b>\n\n"
              "Введіть час рекламного топу в форматі\n"
              "<code>hh:mm</code>\n\n"
              "Поточне повідомлення:\n"
              "{message}"),
            MessageInput(
                handle_time_input,
                filter=F.text & ~F.text.startswith('/')
            ),
            Row(
                Back(Const("◀️ Назад")),
                Button(Const("🔄 Скинути"), id="reset_time", on_click=reset_ad_time),
            ),
            state=CreateFlowMenu.ad_time_settings,
            parse_mode=ParseMode.HTML,
            getter=ad_time_getter
        ),
        Window(
            Format("📊 <b>Налаштування об'єму флоу</b>\n\n"
                "Оберіть кількість останніх постів,\n"
                "яку треба зберігати у флоу:\n\n"
                "Поточне значення: {current_value}"),
            Column(
                Select(
                    text=Format("{item}"),
                    items="volume_options",
                    item_id_getter=lambda x: x,
                    id="volume_select",
                    on_click=on_volume_selected,
                ),
            ),
            Row(
                Button(
                    Const("✏️ Вказати своє число"), 
                    id="custom_volume", 
                    on_click=open_custom_volume_input
                ),
            ),
            Row(
                Back(Const("◀️ Назад")),
            ),
            state=CreateFlowMenu.flow_volume_settings,
            parse_mode=ParseMode.HTML,
            getter=flow_volume_getter
        ),
        Window(
            Const("✏️ <b>Введіть власне число</b>\n\n"
                "Діапазон: 1-50\n\n"
                "Або натисніть 'Назад'"),
            MessageInput(
                handle_custom_volume_input,
                filter=F.text & ~F.text.startswith('/')
            ),
            Row(
                Back(Const("◀️ Назад")),
            ),
            state=CreateFlowMenu.custom_volume_input,
            parse_mode=ParseMode.HTML
        ),
        Window(
            Format("✍️ <b>Налаштування підпису до постів</b>\n\n"
                "Поточний підпис:\n"
                "{current_signature}\n\n"
                "Відправте новий підпис або натисніть 'Пропустити'"),
            MessageInput(
                handle_signature_input,
                filter=F.text & ~F.text.startswith('/')
            ),
            Row(
                Button(Const("⏩ Пропустити"), id="skip_signature", on_click=skip_signature),
                Back(Const("◀️ Назад")),
            ),
            state=CreateFlowMenu.signature_settings,
            parse_mode=ParseMode.HTML,
            getter=signature_getter
        ),
        Window(
            Format("🎉 <b>Вітаю! Ваш флоу створений!</b>\n\n"
                "Зміни можна внести в налаштуваннях\n\n"
                "<b>Параметри Flow \"{flow_name}\":</b>\n"
                "Тематика: {theme}\n"
                "Джерела ({source_count}):\n{sources}\n"
                "Частота генерації: {frequency}\n"
                "Кількість знаків: {words_limit}\n"
                "Виділення заголовка: {title_highlight}\n"
                "Підпис до постів: {signature}\n\n"
                "ID: {flow_id}"),
            Column(
                Button(Const("🔙 До налаштувань"), id="to_settings", on_click=open_flow_settings),
                Button(Const("🏠 В головне меню"), id="to_main", on_click=go_back_to_main),
            ),
            state=CreateFlowMenu.confirmation,
            parse_mode=ParseMode.HTML,
            getter=flow_confirmation_getter
        ),
        Window(
            Const("Відправьте лінк з обраного джерела за шаблоном"),
            Column(
                Button(Const("НАЗВА ДЖЕРЕЛА1"), id="source1", on_click=on_existing_source_selected),
                Button(Const("НАЗВА ДЖЕРЕЛА2"), id="source2", on_click=on_existing_source_selected),
                Button(Const("+ДОДАТИ НОВИЙ ТИП"), id="add_new_source_type", on_click=on_add_new_source_type),
            ),
            Row(
                Button(Const("🔙 Назад"), id='on_create_flow', on_click=on_create_flow),
            ),
            Row(
                Button(Const("В головне меню"), id="go_back_to_main", on_click=go_back_to_main)
            ),
            TextInput(
                id="source_link_input",
                on_success=on_source_link_entered,
            ),
            state=CreateFlowMenu.add_source_link,
            parse_mode=ParseMode.MARKDOWN_V2,
        ),
    )