import logging
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode

from bot.containers import Container

from .states import FlowMenu



async def on_publish_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    post_id = manager.dialog_data.get("current_post_id")
    post_service = Container.post_service()
    await post_service.publish_post(post_id)
    await callback.answer(f"Пост {post_id} опубликован!")
    await manager.show()

async def on_edit_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    post_id = manager.dialog_data.get("current_post_id")
    await callback.answer(f"Редактирование поста {post_id}")

async def on_schedule_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    post_id = manager.dialog_data.get("current_post_id")
    # Здесь можно открыть диалог выбора даты публикации
    await callback.answer(f"Запланировать публикацию поста {post_id}")

async def on_save_to_buffer(callback: CallbackQuery, button: Button, manager: DialogManager):
    post_id = manager.dialog_data.get("current_post_id")
    post_service = Container.post_service()
    await post_service.save_to_buffer(post_id)
    await callback.answer("Пост сохранен в буфер!")