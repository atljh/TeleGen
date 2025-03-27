from aiogram.types import CallbackQuery, Message
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.input import TextInput

from utils.validation import is_valid_link
from .states import CreateFlowMenu

async def on_instagram(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data['selected_source'] = 'instagram'
    await callback.answer("Обрано Instagram")
    await manager.switch_to(CreateFlowMenu.add_source_link)

async def on_facebook(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data['selected_source'] = 'facebook'
    await callback.answer("Обрано Facebook")
    await manager.switch_to(CreateFlowMenu.add_source_link)

async def on_web(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data['selected_source'] = 'web'
    await callback.answer("Обрано Web")
    await manager.switch_to(CreateFlowMenu.add_source_link)

async def on_telegram(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data['selected_source'] = 'telegram'
    await callback.answer("Обрано telegram")
    await manager.switch_to(CreateFlowMenu.add_source_link)


async def on_once_a_day(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data['selected_frequency'] = 'once_a_day'
    await callback.answer("Раз на день")
    await manager.switch_to(CreateFlowMenu.select_words_limit)

async def on_once_a_12(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data['selected_frequency'] = 'once_a_12'
    await callback.answer("Раз на 12 годин")
    await manager.switch_to(CreateFlowMenu.select_words_limit)

async def on_once_an_hour(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data['selected_frequency'] = 'once_an_hour'
    await callback.answer("Раз на годину")
    await manager.switch_to(CreateFlowMenu.select_words_limit)



async def on_source_link_entered(
    message: Message, 
    widget: TextInput, 
    manager: DialogManager, 
    data: str
):
    if not is_valid_link(data):
        await message.answer("Невірний формат посилання!")
        return
    
    manager.dialog_data['source_link'] = data
    await manager.switch_to(CreateFlowMenu.message_preview)

async def on_existing_source_selected(
    callback: CallbackQuery, 
    button: Button, 
    manager: DialogManager
):
    source_name = button.widget_id
    manager.dialog_data['selected_source'] = source_name
    await callback.answer(f"Обрано {source_name}")
    await manager.switch_to(CreateFlowMenu.message_preview)

async def on_add_new_source_type(
    callback: CallbackQuery, 
    button: Button, 
    manager: DialogManager
):
    await manager.switch_to(CreateFlowMenu.select_source)
    await callback.answer("Оберіть новий тип джерела")