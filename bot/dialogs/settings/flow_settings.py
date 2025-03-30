from aiogram import F
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, Window, Dialog
from aiogram_dialog.widgets.kbd import Button, Back, SwitchTo, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Row, Back, Group, Select, Column, Next, SwitchTo

from .states import SettingsMenu

# ================== ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ ФЛОУ ==================

async def open_flow_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    """Открывает настройки флоу"""
    await manager.switch_to(SettingsMenu.flow_settings)

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