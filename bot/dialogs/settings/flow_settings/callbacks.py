import logging
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode, Window, Dialog
from aiogram_dialog.widgets.kbd import Button

from .states import FlowSettingsMenu
from dialogs.settings.states import SettingsMenu

# ================== ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ ФЛОУ ==================

async def start_flow_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    selected_channel = manager.dialog_data.get("selected_channel")
    logging.info(selected_channel)
    await manager.start(
        FlowSettingsMenu.flow_settings,
        data={"selected_channel": selected_channel},
        mode=StartMode.RESET_STACK 
    )

async def open_flow_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowSettingsMenu.flow_settings)

async def open_main_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    selected_channel = manager.dialog_data.get("selected_channel")
    await manager.start(
        SettingsMenu.channel_settings,
        data={"selected_channel": selected_channel},
        mode=StartMode.RESET_STACK 
    )


# ================== ОСНОВНЫЕ ОБРАБОТЧИКИ ФЛОУ ==================

async def set_generation_frequency(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowSettingsMenu.generation_frequency)

async def set_character_limit(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowSettingsMenu.character_limit)

async def toggle_title_highlight(callback: CallbackQuery, button: Button, manager: DialogManager):
    current = manager.dialog_data.get("title_highlight", False)
    manager.dialog_data["title_highlight"] = not current
    await callback.answer(f"Виділення заголовку {'увімкнено' if not current else 'вимкнено'}")

async def configure_ad_block(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowSettingsMenu.ad_block_settings)

async def set_posts_in_flow(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowSettingsMenu.posts_in_flow)

async def open_source_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowSettingsMenu.source_settings)


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
        await manager.switch_to(FlowSettingsMenu.custom_frequency_input)
    
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
    await manager.switch_to(FlowSettingsMenu.exact_limit_input)
    await callback.answer("Введіть число від 100 до 10000")

async def handle_exact_limit_input(message: Message, widget, dialog_manager: DialogManager):
    try:
        limit = int(message.text)
        if 100 <= limit <= 10000:
            dialog_manager.dialog_data["char_limit"] = limit
            await dialog_manager.switch_to(FlowSettingsMenu.character_limit)
            await message.answer(f"Ліміт оновлено до {limit} знаків")
        else:
            await message.answer("Будь ласка, введіть число від 100 до 10000")
    except ValueError:
        await message.answer("Будь ласка, введіть коректне число")

async def toggle_ad_block(callback: CallbackQuery, button: Button, manager: DialogManager):
    ad_enabled = button.widget_id == "enable_ads"
    manager.dialog_data["ad_enabled"] = ad_enabled
    await callback.answer(f"Рекламний блок {'увімкнено' if ad_enabled else 'вимкнено'}")
    await manager.switch_to(FlowSettingsMenu.flow_settings)

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
    await manager.switch_to(FlowSettingsMenu.exact_posts_input)
    await callback.answer("Введіть число від 1 до 10")

async def handle_exact_posts_input(message: Message, widget, dialog_manager: DialogManager):
    try:
        count = int(message.text)
        if 1 <= count <= 10:
            dialog_manager.dialog_data["posts_count"] = count
            await dialog_manager.switch_to(FlowSettingsMenu.posts_in_flow)
            await message.answer(f"✅ Встановлено: {count} постів")
        else:
            await message.answer("⚠️ Введіть число від 1 до 10")
    except ValueError:
        await message.answer("❌ Введіть коректне число")