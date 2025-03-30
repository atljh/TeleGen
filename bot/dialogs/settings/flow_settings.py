from aiogram import F
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, Window, Dialog
from aiogram_dialog.widgets.kbd import Button, Back, SwitchTo, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Row, Back, Group, Select, Column, Next, SwitchTo

from .states import SettingsMenu
from .callbacks import confirm_delete_channel

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
    await manager.back()

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
            Button(Const("🗑 Видалити канал"), id="delete_channel", on_click=confirm_delete_channel),
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

def create_character_limit_window():
    return Window(
        Format(
            "🔠 <b>Обмеження по знакам</b>\n\n"
            "Поточний ліміт: {char_limit} знаків\n\n"
            "Оберіть дію:"
        ),
        Column(
            Button(Const("➕ Збільшити"), id="increase_limit"),
            Button(Const("➖ Зменшити"), id="decrease_limit"),
            Button(Const("✏️ Вказати точне число"), id="set_exact_limit"),
            Button(Const("♾ Вимкнути обмеження"), id="disable_limit"),
        ),
        Row(
            Button(Const("◀️ Назад"), id="open_flow_settings", on_click=open_flow_settings),
        ),
        state=SettingsMenu.character_limit,
        parse_mode=ParseMode.HTML,
        getter=character_limit_getter
    )