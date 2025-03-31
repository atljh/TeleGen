from aiogram import F
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, Window, Dialog
from aiogram_dialog.widgets.kbd import Button, Back, SwitchTo, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Row, Back, Group, Select, Column, Next, SwitchTo
from aiogram_dialog.widgets.input import TextInput, MessageInput

from .states import SettingsMenu
from .callbacks import confirm_delete_channel

import logging

# ================== ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ ФЛОУ ==================

async def open_flow_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.flow_settings)

async def open_main_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.main)

# ================== ОСНОВНЫЕ ОБРАБОТЧИКИ ФЛОУ ==================

async def set_generation_frequency(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.generation_frequency)

async def set_character_limit(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.character_limit)

async def toggle_title_highlight(callback: CallbackQuery, button: Button, manager: DialogManager):
    current = manager.dialog_data.get("title_highlight", False)
    manager.dialog_data["title_highlight"] = not current
    await callback.answer(f"Виділення заголовку {'увімкнено' if not current else 'вимкнено'}")

async def configure_ad_block(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.ad_block_settings)

async def set_posts_in_flow(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.posts_in_flow)

async def open_source_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.source_settings)


# ================== ОБРАБОТЧИКИ ПОД-НАСТРОЕК ==================

async def set_frequency(callback: CallbackQuery, button: Button, manager: DialogManager):
    freq_map = {
        "freq_3h": 3,
        "freq_6h": 6,
        "freq_12h": 12,
        "freq_24h": 24
    }
    
    if button.widget_id in freq_map:
        manager.dialog_data["generation_freq"] = freq_map[button.widget_id]
        await callback.answer(f"Частоту встановлено: кожні {freq_map[button.widget_id]} годин")
    else:
        await manager.switch_to(SettingsMenu.custom_frequency_input)
    
    await manager.back()

async def adjust_character_limit(callback: CallbackQuery, button: Button, manager: DialogManager):
    current = manager.dialog_data.get("char_limit", 1000)
    
    if button.widget_id == "increase_limit":
        new_limit = current + 100
    elif button.widget_id == "decrease_limit":
        new_limit = max(100, current - 100)
    elif button.widget_id == "disable_limit":
        new_limit = 0
    
    manager.dialog_data["char_limit"] = new_limit
    action = {
        "increase_limit": "збільшено",
        "decrease_limit": "зменшено",
        "disable_limit": "вимкнено"
    }.get(button.widget_id, "змінено")
    
    await callback.answer(f"Ліміт {action} до {new_limit if new_limit > 0 else '∞'} знаків")
    await manager.show()
    

async def set_exact_limit(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.exact_limit_input)
    await callback.answer("Введіть число від 100 до 10000")

async def handle_exact_limit_input(message: Message, widget, dialog_manager: DialogManager):
    try:
        limit = int(message.text)
        if 100 <= limit <= 10000:
            dialog_manager.dialog_data["char_limit"] = limit
            await dialog_manager.switch_to(SettingsMenu.character_limit)
            await message.answer(f"Ліміт оновлено до {limit} знаків")
        else:
            await message.answer("Будь ласка, введіть число від 100 до 10000")
    except ValueError:
        await message.answer("Будь ласка, введіть коректне число")

async def toggle_ad_block(callback: CallbackQuery, button: Button, manager: DialogManager):
    ad_enabled = button.widget_id == "enable_ads"
    manager.dialog_data["ad_enabled"] = ad_enabled
    await callback.answer(f"Рекламний блок {'увімкнено' if ad_enabled else 'вимкнено'}")
    await manager.switch_to(SettingsMenu.flow_settings)

async def adjust_posts_count(callback: CallbackQuery, button: Button, manager: DialogManager):
    current = manager.dialog_data.get("posts_count", 1)
    if button.widget_id == "increase_posts":
        new_count = min(10, current + 1)
    else:
        new_count = max(1, current - 1)
    
    manager.dialog_data["posts_count"] = new_count
    await callback.answer(f"Кількість постів: {new_count}")
    await manager.show()


async def set_exact_posts_count(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.exact_posts_input)
    await callback.answer("Введіть число від 1 до 10")

async def handle_exact_posts_input(message: Message, widget, dialog_manager: DialogManager):
    try:
        count = int(message.text)
        if 1 <= count <= 10:
            dialog_manager.dialog_data["posts_count"] = count
            await dialog_manager.switch_to(SettingsMenu.posts_in_flow)
            await message.answer(f"✅ Встановлено: {count} постів")
        else:
            await message.answer("⚠️ Введіть число від 1 до 10")
    except ValueError:
        await message.answer("❌ Введіть коректне число")

# ================== ОКНА НАСТРОЕК ФЛОУ ==================
def create_flow_settings_window():
    return Window(
        Format(
            "🔄 <b>НАЛАШТУВАННЯ ФЛОУ</b>\n\n"
            "📢 <b>Канал:</b> {dialog_data[selected_channel].name}\n\n"
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
            Button(Const("◀️ Назад"), id="open_main_settings", on_click=open_main_settings),
        ),
        state=SettingsMenu.flow_settings,
        parse_mode=ParseMode.HTML,
        getter=flow_settings_getter
    )

async def character_limit_getter(dialog_manager: DialogManager, **kwargs):
    return {
        "char_limit": dialog_manager.dialog_data.get("char_limit", 1000)
    }

async def flow_settings_getter(dialog_manager: DialogManager, **kwargs):
    current = dialog_manager.dialog_data.get("title_highlight", False)
    return {
        "highlight_status": "✅ увімкнено" if current else "❌ вимкнено"
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
            Button(Const("◀️ Назад"), id="open_flow_settings", on_click=open_flow_settings),
        ),
        state=SettingsMenu.ad_block_settings,
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
            Button(Const("◀️ Назад"), id="open_flow_settings", on_click=open_flow_settings),
        ),
        state=SettingsMenu.generation_frequency,
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
            Button(Const("◀️ Назад"), id="open_flow_settings", on_click=open_flow_settings),
        ),
        state=SettingsMenu.exact_limit_input,
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
                Const("◀️ Назад"), 
                id="open_flow_settings", 
                on_click=open_flow_settings
            ),
        ),
        state=SettingsMenu.character_limit,
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
            Button(Const("◀️ Назад"), id="open_flow_settings", on_click=open_flow_settings),        
        ),
        state=SettingsMenu.posts_in_flow,
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
        Button(Const("◀️ Назад"), id="open_flow_settings", on_click=open_flow_settings),
        state=SettingsMenu.exact_posts_input,
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
        Button(Const("◀️ Назад"), id="open_flow_settings", on_click=open_flow_settings),    
        state=SettingsMenu.source_settings,
        parse_mode=ParseMode.HTML
    )