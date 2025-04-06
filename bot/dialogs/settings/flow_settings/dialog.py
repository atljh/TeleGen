from aiogram import F
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, Window, Dialog
from aiogram_dialog.widgets.kbd import Button, Back, SwitchTo, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Row, Back, Group, Select, Column, Next, SwitchTo
from aiogram_dialog.widgets.input import TextInput, MessageInput

from .states import FlowSettingsMenu
from .callbacks import (
    set_character_limit,
    set_exact_limit,
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
    handle_exact_limit_input,
    adjust_character_limit,
    adjust_posts_count
)

def create_flow_settings_window():
    return Window(
        Format(
            "🔄 <b>НАЛАШТУВАННЯ ФЛОУ</b>\n\n"
            "📢 <b>Канал: {channel_name}</b>\n\n"
        ),
        Column(
            Button(Const("⏱ Частота генерації"), id="generation_frequency", on_click=set_generation_frequency),
            Button(Const("🔠 Обмеження по знакам"), id="character_limit", on_click=set_character_limit),
            Button(
                Format("📌 Виділення заголовку: {highlight_status}"), 
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


async def flow_settings_getter(dialog_manager: DialogManager, **kwargs):
    selected_channel = (
        dialog_manager.start_data.get("selected_channel") 
        or dialog_manager.dialog_data.get("selected_channel")
    )
    
    if selected_channel:
        dialog_manager.dialog_data["selected_channel"] = selected_channel
    
    return {
        "channel_name": selected_channel.name,
        "highlight_status": "✅ увімкнено" if dialog_manager.dialog_data.get("title_highlight", False) else "❌ вимкнено"
    }

async def character_limit_getter(dialog_manager: DialogManager, **kwargs):
    return {
        "char_limit": dialog_manager.dialog_data.get("char_limit", 1000)
    }

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
            Button(Const("🕒 Кожні 3 години"), id="freq_3h"),
            Button(Const("🕕 Кожні 6 годин"), id="freq_6h"),
            Button(Const("🕘 Кожні 12 годин"), id="freq_12h"),
            Button(Const("🌙 Раз на день"), id="freq_24h"),
            Button(Const("✏️ Вказати власний інтервал"), id="custom_freq"),
        ),
        Row(
            Button(Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings),
        ),
        state=FlowSettingsMenu.generation_frequency,
        parse_mode=ParseMode.HTML,
    )

def create_exact_limit_input_window():
    return Window(
        Const("✏️ <b>Введіть точний ліміт символів</b>\n\n"
             "Допустимий діапазон: 100-10000\n\n"
             "Або натисніть 'Назад' для скасування"),
        MessageInput(
            handle_exact_limit_input,
            filter=F.text,
        ),
        Row(
            Button(Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings),
        ),
        state=FlowSettingsMenu.exact_limit_input,
        parse_mode=ParseMode.HTML
    )

def create_character_limit_window():
    return Window(
        Format(
            "🔠 <b>Обмеження по знакам</b>\n\n"
            "Поточний ліміт: {char_limit} знаків\n\n"
            "Оберіть дію:"
        ),
        Column(
            Button(
                Const("➕ Збільшити"), 
                id="increase_limit", 
                on_click=adjust_character_limit
            ),
            Button(
                Const("➖ Зменшити"), 
                id="decrease_limit", 
                on_click=adjust_character_limit
            ),
            Button(
                Const("✏️ Вказати точне число"), 
                id="set_exact_limit",
                on_click=set_exact_limit
            ),
            Button(
                Const("♾ Вимкнути обмеження"), 
                id="disable_limit",
                on_click=adjust_character_limit
            ),
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

async def posts_in_flow_getter(dialog_manager: DialogManager, **kwargs):
    return {
        "posts_count": dialog_manager.dialog_data.get("posts_count", 1)
    }

def create_posts_in_flow_window():
    return Window(
        Format("📊 <b>Кількість постів у флоу</b>\n\nПоточне значення: {posts_count}"),
        Column(
            Button(Const("➕ Збільшити"), id="increase_posts", on_click=adjust_posts_count),
            Button(Const("➖ Зменшити"), id="decrease_posts", on_click=adjust_posts_count),
            Button(Const("✏️ Вказати точне число"), id="set_exact_posts", on_click=set_exact_posts_count),
        ),
        Row(
            Button(Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings),        
        ),
        state=FlowSettingsMenu.posts_in_flow,
        parse_mode=ParseMode.HTML,
        getter=posts_in_flow_getter
    )

def create_exact_posts_input_window():
    return Window(
        Const("✏️ <b>Введіть кількість постів</b>\n(1-10)"),
        MessageInput(
            handle_exact_posts_input,
            filter=F.text & ~F.text.startswith('/')
        ),
        Button(Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings),
        state=FlowSettingsMenu.exact_posts_input,
        parse_mode=ParseMode.HTML
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
        create_exact_limit_input_window(),
        create_ad_block_settings_window(),
        create_posts_in_flow_window(),
        create_source_settings_window(),
        create_exact_posts_input_window()
    )