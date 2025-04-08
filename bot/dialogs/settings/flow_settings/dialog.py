import logging
from aiogram import F
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, Window, Dialog
from aiogram_dialog.widgets.kbd import Button, Back, SwitchTo, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Column, Row, Select, ScrollingGroup
from aiogram_dialog.widgets.input import TextInput, MessageInput

from .getters import (
    character_limit_getter,
    flow_settings_getter,
    get_current_source,
    get_source_type,
    get_sources_data,
    posts_in_flow_getter,
)
from .states import FlowSettingsMenu
from .callbacks import (
    back_to_settings,
    character_limit,
    on_source_link_entered,
    on_source_selected_for_delete,
    on_source_selected_for_edit,
    set_frequency,
    set_generation_frequency,
    set_posts_in_flow,
    to_add_source,
    to_select_source_to_delete,
    to_select_source_to_edit,
    toggle_ad_block,
    toggle_title_highlight,
    configure_ad_block,
    open_flow_settings,
    open_main_settings,
    open_source_settings,
    set_character_limit,
    set_flow_volume
)

def create_flow_settings_window():
    return Window(
        Format(
        """
        <b>Канал:</b> {channel_name}
                
        <b><u>Параметри Flow</u></b>
        - <b>Тематика:</b> {theme}
        - <b>Джерела ({source_count}):</b>
            <b>{sources}</b>
        - <b>Частота генерації:</b> {frequency}
        - <b>Кількість знаків:</b> {words_limit}
        - <b>Кількість постів у флоу:</b> {flow_volume}
        - <b>Виділення заголовка:</b> {title_highlight}
        - <b>Підпис до постів:</b> {signature}
        """
        ),
        Column(
            Button(Const("⏱ Частота генерації"), id="generation_frequency", on_click=set_generation_frequency),
            Button(Const("🔠 Обмеження по символам"), id="character_limit", on_click=character_limit),
            Button(
                Format("📌 Виділення заголовку: {title_highlight}"), 
                id="title_highlight", 
                on_click=toggle_title_highlight
            ),
            Button(Const("📢 Рекламний блок"), id="ad_block", on_click=configure_ad_block),
            Button(Const("📊 Кількість постів у флоу"), id="posts_in_flow", on_click=set_posts_in_flow),
            Button(Const("📚 Налаштування джерел"), id="source_settings", on_click=open_source_settings),
        ),
        Row(
            Button(Const("🔙 Назад"), id="open_main_settings", on_click=open_main_settings),
        ),
        state=FlowSettingsMenu.flow_settings,
        parse_mode=ParseMode.HTML,
        getter=flow_settings_getter
    )


def create_ad_block_settings_window():
    return Window(
        Const("📢 <b>Налаштування рекламного блоку</b>"),
        Column(
            Button(
                Const("✅ Включити рекламу"), 
                id="enable_ads",
                on_click=toggle_ad_block
            ),
            Button(
                Const("❌ Вимкнути рекламу"), 
                id="disable_ads",
                on_click=toggle_ad_block
            ),
        ),
        Row(
            Button(Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings),
        ),
        state=FlowSettingsMenu.ad_block_settings,
        parse_mode=ParseMode.HTML
    )

def create_frequency_settings_window():
    return Window(
        Const("⏱ <b>Налаштування частоти генерації</b>\n\n"
             "Оберіть як часто бот буде генерувати пости:"),
        Column(
            Button(Const("Кожну годину"), id="freq_1h", on_click=set_frequency),
            Button(Const("Кожні 12 годин"), id="freq_12h", on_click=set_frequency),
            Button(Const("Раз на день"), id="freq_24h", on_click=set_frequency),
        ),
        Row(
            Button(Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings),
        ),
        state=FlowSettingsMenu.generation_frequency,
        parse_mode=ParseMode.HTML,
    )

def create_character_limit_window():
    return Window(
        Format(
            "🔠 <b>Обмеження по знакам</b>\n\n"
            "Поточний ліміт: {char_limit} знаків\n\n"
            "Оберіть дію:"
        ),
        Column(
            Button(Const("До 100"), id="limit_100", on_click=set_character_limit),
            Button(Const("До 300"), id="limit_300", on_click=set_character_limit),
            Button(Const("До 1000"), id="limit_1000", on_click=set_character_limit),
        ),
        Row(
            Button(
                Const("🔙 Назад"), 
                id="open_flow_settings", 
                on_click=open_flow_settings
            ),
        ),
        state=FlowSettingsMenu.character_limit,
        parse_mode=ParseMode.HTML,
        getter=character_limit_getter
    )

def create_posts_in_flow_window():
    return Window(
        Format("📊 <b>Кількість постів у флоу</b>\n\nПоточне значення: {posts_count}"),
        Column(
            Button(Const("5"), id="volume_5", on_click=set_flow_volume),
            Button(Const("10"), id="volume_10", on_click=set_flow_volume),
            Button(Const("20"), id="volume_20", on_click=set_flow_volume),
        ),
        Row(
            Button(Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings),        
        ),
        state=FlowSettingsMenu.posts_in_flow,
        parse_mode=ParseMode.HTML,
        getter=posts_in_flow_getter
    )
    
def create_sources_dialog():
    return Dialog(
        Window(
            Format(
                "<b>Управління джерелами</b>\n\n"
                "Кількість джерел: {count}\n\n"
                "{sources_list}"
            ),
            Column(
                Button(Const("➕ Додати джерело"), id="add_source", on_click=to_add_source),
                Button(Const("✏️ Редагувати джерело"), id="edit_source", on_click=to_select_source_to_edit),
                Button(Const("🗑 Видалити джерело"), id="delete_source", on_click=to_select_source_to_delete),
            ),
            Button(Const("🔙 Назад"), id="back_to_settings", on_click=back_to_settings),
            state=FlowSettingsMenu.source_settings,
            parse_mode=ParseMode.HTML,
            getter=get_sources_data
        ),
        
        Window(
            Const("Виберіть тип джерела:"),
            Column(
                Button(Const("📷 Instagram"), id="source_instagram"),
                Button(Const("🌐 Веб-сайт"), id="source_web"),
                Button(Const("📺 YouTube"), id="source_youtube"),
            ),
            Back(Const("◀️ Назад")),
            state=FlowSettingsMenu.add_source,
        ),
        
        Window(
            Format("Введіть посилання для {source_type}:"),
            TextInput(
                id="source_link_input",
                on_success=on_source_link_entered
            ),
            Back(Const("◀️ Назад")),
            state=FlowSettingsMenu.add_source_link,
            getter=get_source_type
        ),
        
        Window(
            Const("Оберіть джерело для редагування:"),
            ScrollingGroup(
                Select(
                    Format("{item[type]} - {item[link]}"),
                    id="sources_select",
                    item_id_getter=lambda item: item["id"],
                    items="sources",
                    on_click=on_source_selected_for_edit,
                ),
                width=1,
                height=5,
                id='edit_select'
            ),
            Back(Const("◀️ Назад")),
            state=FlowSettingsMenu.select_source_to_edit,
            getter=get_sources_data
        ),
        
        Window(
            Format("Редагування джерела:\n{source[type]} - {source[link]}"),
            Column(
                Button(Const("✏️ Змінити посилання"), id="edit_link"),
                Button(Const("♻️ Змінити тип"), id="edit_type"),
            ),
            Back(Const("◀️ Назад")),
            state=FlowSettingsMenu.edit_source,
            getter=get_current_source
        ),
        
        Window(
            Const("Оберіть джерело для видалення:"),
            ScrollingGroup(
                Select(
                    Format("{item[type]} - {item[link]}"),
                    id="sources_select",
                    item_id_getter=lambda item: item["id"],
                    items="sources",
                    on_click=on_source_selected_for_delete,
                ),
                width=1,
                height=5,
                id='delete_select'
            ),
            Back(Const("◀️ Назад")),
            state=FlowSettingsMenu.select_source_to_delete,
            getter=get_sources_data
        ),
    )

def create_flow_settings_dialog():
    return Dialog(
        create_flow_settings_window(),
        create_frequency_settings_window(),
        create_character_limit_window(),
        create_ad_block_settings_window(),
        create_posts_in_flow_window(),
    )