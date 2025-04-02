import logging
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode

from .states import FlowMenu

async def on_publish_now(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowMenu.publish_now)

async def on_schedule(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowMenu.schedule)

async def on_edit(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowMenu.edit)

async def on_save_to_buffer(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowMenu.save_to_buffer)
    
async def on_refresh_posts(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager
):
    await manager.show()
    await callback.answer("Список постів оновлено")

async def on_post_select(
    callback: CallbackQuery, 
    widget, 
    manager: DialogManager, 
    item_id: str
):
    manager.dialog_data["selected_post_id"] = int(item_id)
    await manager.switch_to(FlowMenu.post_detail)

async def on_scroll(callback: CallbackQuery, widget, manager: DialogManager):
    # Логика прокрутки (автоматически обрабатывается StubScroll)
    await manager.dialog().next()

async def handle_post_action(
    callback: CallbackQuery, 
    button: Button, 
    manager: DialogManager
):
    # Извлекаем ID поста и действие из ID кнопки
    btn_id = button.widget_id
    action, post_id = btn_id.split("_", 1)
    
    # Сохраняем выбранный пост
    manager.dialog_data["selected_post_id"] = post_id
    
    # if action == "publish":
    #     # await publish_post(post_id)
    # elif action == "edit":
    #     await manager.switch_to(FlowMenu.post_edit)
    # elif action == "buffer":
    #     await save_to_buffer(post_id)
    
    await callback.answer(f"Действие: {action} для поста {post_id}")