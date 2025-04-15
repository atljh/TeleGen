import logging
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode

from bot.containers import Container
from bot.database.exceptions import InvalidOperationError

from .states import FlowMenu
from .getters import paging_getter
from bot.tasks import check_flows_generation


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
    
    try:
        updated_post = await post_service.publish_post(post_id, channel.channel_id)
        manager.dialog_data["post"] = {
            **current_post,
            "status": "✅ Опубліковано",
            "pub_time": updated_post.publication_date.strftime("%d.%m.%Y %H:%M"),
            "is_published": True
        }
        await callback.answer(f"Пост {post_id} успiшно опублiковано в канал!")
    except InvalidOperationError as e:
        await callback.answer(str(e), show_alert=True)
    except Exception as e:
        await callback.answer(f"Помилка: {str(e)}", show_alert=True)
        logging.exception("Помилка при публікації посту")

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

async def on_force_generate(callback: CallbackQuery, button: Button, manager: DialogManager):
    
    try:
        check_flows_generation.delay()
        await callback.answer("Генерацiя")
    except Exception as e:
        await callback.answer(f"Помилка: {str(e)}", show_alert=True)