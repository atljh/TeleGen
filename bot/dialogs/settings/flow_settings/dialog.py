import logging
from aiogram import F
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, Window, Dialog
from aiogram_dialog.widgets.kbd import Button, Back, SwitchTo, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Row, Back, Group, Select, Column, Next, SwitchTo
from aiogram_dialog.widgets.input import TextInput, MessageInput

from bot.dialogs.settings.flow_settings.getters import character_limit_getter, flow_settings_getter, posts_in_flow_getter

from .states import FlowSettingsMenu
from .callbacks import (
    character_limit,
    set_exact_posts_count,
    set_frequency,
    set_generation_frequency,
    set_posts_in_flow,
    toggle_ad_block,
    toggle_title_highlight,
    configure_ad_block,
    open_flow_settings,
    open_main_settings,
    open_source_settings,
    handle_exact_posts_input,
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
    
def create_source_settings_window():
    return Window(
        Const("📚 <b>Налаштування джерел</b>"),
        Column(
            Button(Const("➕ Додати джерело"), id="add_source"),
            Button(Const("✏️ Редагувати джерела"), id="edit_sources"),
            Button(Const("🗑 Видалити джерело"), id="delete_source"),
        ),
        Button(Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings),    
        state=FlowSettingsMenu.source_settings,
        parse_mode=ParseMode.HTML
    )

def create_flow_settings_dialog():
    return Dialog(
        create_flow_settings_window(),
        create_frequency_settings_window(),
        create_character_limit_window(),
        create_ad_block_settings_window(),
        create_posts_in_flow_window(),
        create_source_settings_window(),
    )