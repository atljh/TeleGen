import logging
from typing import Dict
from aiogram.types import CallbackQuery, Message, ForceReply, ContentType
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode

from bot.containers import Container
from bot.database.exceptions import InvalidOperationError

from bot.dialogs.generation.flow.states import FlowMenu
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


#===========================================EDIT===========================================
async def on_edit_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    data = await paging_getter(manager)
    post_data = data["post"]
    
    manager.dialog_data["editing_post"] = post_data
    
    await manager.switch_to(FlowMenu.edit_post)

async def on_edit_text(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer(
        "Надішліть новий текст для поста:",
        reply_markup=ForceReply(selective=True)
    )
    manager.dialog_data["awaiting_input"] = "text"

async def on_edit_media(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer(
        "Надішліть нове фото або відео для поста:",
        reply_markup=ForceReply(selective=True)
    )
    manager.dialog_data["awaiting_input"] = "media"


async def process_edit_input(message: Message, widget, manager: DialogManager):
    input_type = manager.dialog_data.get("awaiting_input")
    
    if input_type == "text":
        manager.dialog_data["edited_content"] = message.text
        await message.answer("Текст успішно змінено!")
        
    elif input_type == "media":
        if message.content_type == ContentType.PHOTO:
            file_id = message.photo[-1].file_id
            manager.dialog_data["edited_media"] = {
                "type": "photo",
                "file_id": file_id
            }
            await message.answer("Фото успішно змінено!")
            
        elif message.content_type == ContentType.VIDEO:
            file_id = message.video.file_id
            manager.dialog_data["edited_media"] = {
                "type": "video",
                "file_id": file_id
            }
            await message.answer("Відео успішно змінено!")
        else:
            await message.answer("Будь ласка, надішліть фото або відео")
            return
    
    try:
        await message.bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id - 1
        )
    except:
        pass
    
    manager.dialog_data.pop("awaiting_input", None)
    await manager.show()

async def on_schedule_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    post_id = manager.dialog_data.get("current_post_id")
    await callback.answer(f"Запланувати публікацію поста {post_id}")

async def on_save_to_buffer(callback: CallbackQuery, button: Button, manager: DialogManager):
    post_id = manager.dialog_data.get("current_post_id")
    # post_service = Container.post_service()
    # await post_service.save_to_buffer(post_id)
    await callback.answer("Пост збережено в буфер!")
