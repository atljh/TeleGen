import logging
from typing import Dict
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode

from bot.containers import Container
from bot.database.exceptions import InvalidOperationError

from .states import FlowMenu
from .getters import paging_getter, send_media_album


async def on_publish_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    dialog_data = await paging_getter(manager)
    start_data = manager.start_data or {}

    current_post = dialog_data["post"]
    post_id = current_post["id"]
    
    channel = start_data.get("selected_channel") or dialog_data.get("selected_channel")
    
    if not channel:
        await callback.answer("Канал не вибрано!")
        return
    
    post_service = Container.post_service()
    is_album = False
    
    try:
        updated_post = await post_service.publish_post(post_id, channel.channel_id)
        is_album = len(updated_post.images) > 1
        
        manager.dialog_data["post"] = {
            **current_post,
            "status": "✅ Опубліковано",
            "pub_time": updated_post.publication_date.strftime("%d.%m.%Y %H:%M"),
            "is_published": True
        }
        
        await callback.answer(f"Пост успiшно опублiковано в канал!")
        
    except InvalidOperationError as e:
        logging.error(e)
        await callback.answer(str(e))
    except Exception as e:
        logging.error(e)
        await callback.answer(f"Помилка: {str(e)}")
        logging.exception("Помилка при публікації посту")
    finally:
        await manager.show()

async def on_edit_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    post_id = manager.dialog_data.get("current_post_id")
    await callback.answer(f"Редагування поста {post_id}")

async def on_schedule_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    post_id = manager.dialog_data.get("current_post_id")
    await callback.answer(f"Запланувати публікацію поста {post_id}")

async def on_save_to_buffer(callback: CallbackQuery, button: Button, manager: DialogManager):
    post_id = manager.dialog_data.get("current_post_id")
    # post_service = Container.post_service()
    # await post_service.save_to_buffer(post_id)
    await callback.answer("Пост збережено в буфер!")


async def on_page_changed(
    callback: CallbackQuery, 
    button: Button, 
    manager: DialogManager
):
    # Получаем текущие данные
    data = await paging_getter(manager)
    
    # Если это альбом - отправляем его
    if data["post"].get("is_album"):
        await send_media_album(manager, data["post"])
    
    # Обновляем диалог (кнопки пагинации и другую информацию)
    await manager.dialog().update(manager)
    
    # Подтверждаем обработку callback
    await callback.answer()