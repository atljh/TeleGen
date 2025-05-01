import os
import logging
from typing import Dict
from aiogram.types import CallbackQuery, Message, ForceReply, ContentType
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode
from django.conf import settings

from bot.containers import Container
from bot.database.dtos.dtos import MediaType, PostImageDTO
from bot.database.exceptions import InvalidOperationError, PostNotFoundError

from bot.dialogs.generation.flow.states import FlowMenu
from .getters import paging_getter, send_media_album


async def on_back_to_posts(callback: CallbackQuery, button: Button, manager: DialogManager):
    selected_channel = manager.dialog_data.get("selected_channel")
    channel_flow = manager.dialog_data.get('channel_flow')
    item_id = manager.dialog_data.get('item_id')

    if not channel_flow:
        await callback.answer(f"У канала {selected_channel.name} поки немає Флоу")
        return
    await manager.start(
        FlowMenu.posts_list,
        data={
            "selected_channel": selected_channel,
            "channel_flow": channel_flow,
            "channel_id": item_id
            },
        mode=StartMode.RESET_STACK 
    )

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
    )
    manager.dialog_data["awaiting_input"] = "text"

async def on_edit_media(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer(
        "Надішліть нове фото або відео для поста:",
    )
    manager.dialog_data["awaiting_input"] = "media"


async def process_edit_input(message: Message, widget, manager: DialogManager):
    input_type = manager.dialog_data.get("awaiting_input")
    post_data = manager.dialog_data.get("editing_post", {})
    post_id = post_data.get("id")
    
    if not post_id:
        await message.answer("Помилка: ID поста не знайдено")
        return

    post_service = Container.post_service()

    try:
        if input_type == "text":
            new_text = message.text
            manager.dialog_data["edited_content"] = new_text
            
            await post_service.update_post(
                post_id=post_id,
                content=new_text
            )
            await message.answer("Текст успішно оновлено!")
            
        elif input_type == "media":
            if message.content_type == ContentType.PHOTO:
                file_id = message.photo[-1].file_id
                file = await message.bot.get_file(file_id)
                file_path = f"posts/images/{file_id}.jpg"
                
                destination = os.path.join(settings.MEDIA_ROOT, file_path)
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                await message.bot.download_file(file.file_path, destination)
                
                updated_post = await post_service.update_post(
                    post_id=post_id,
                    images=[{"file_path": file_path, "order": 0}],
                    video_url=None
                )
                
                manager.dialog_data["edited_media"] = {
                    "type": 'photo',
                    "url": os.path.join(settings.MEDIA_URL, file_path)
                }
                await message.answer("Фото успішно збережено!")
                
            elif message.content_type == ContentType.VIDEO:
                file_id = message.video.file_id
                file = await message.bot.get_file(file_id)
                file_path = f"posts/videos/{file_id}.mp4"
                
                destination = os.path.join(settings.MEDIA_ROOT, file_path)
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                await message.bot.download_file(file.file_path, destination)
                
                await post_service.update_post(
                    post_id=post_id,
                    video_url=os.path.join(settings.MEDIA_URL, file_path),
                    images=[]
                )
                
                manager.dialog_data["edited_media"] = {
                    "type": 'video',
                    "url": os.path.join(settings.MEDIA_URL, file_path)
                }
                await message.answer("Відео успішно збережено!")
            else:
                await message.answer("Будь ласка, надішліть фото або відео")
                return
    
        if input_type == "text":
            manager.dialog_data["editing_post"]["content"] = new_text
        elif input_type == "media":
            if message.content_type == ContentType.PHOTO:
                manager.dialog_data["editing_post"]["images"] = [
                    {"url": os.path.join(settings.MEDIA_URL, file_path), "order": 0}
                ]
                manager.dialog_data["editing_post"]["video_url"] = None
            else:
                manager.dialog_data["editing_post"]["video_url"] = os.path.join(settings.MEDIA_URL, file_path)
                manager.dialog_data["editing_post"]["images"] = []
        
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id - 1
            )
        except:
            pass
            
        manager.dialog_data.pop("awaiting_input", None)
        # await manager.show()
        
    except PostNotFoundError:
        await message.answer("Помилка: пост не знайдено")
    except Exception as e:
        logging.error(f"Помилка збереження: {str(e)}")
        await message.answer("Помилка при збереженні змін")


async def on_schedule_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    post_id = manager.dialog_data.get("current_post_id")
    await callback.answer(f"Запланувати публікацію поста {post_id}")

async def on_save_to_buffer(callback: CallbackQuery, button: Button, manager: DialogManager):
    post_id = manager.dialog_data.get("current_post_id")
    # post_service = Container.post_service()
    # await post_service.save_to_buffer(post_id)
    await callback.answer("Пост збережено в буфер!")



async def open_calendar(callback: CallbackQuery, widget, dialog_manager: DialogManager):
    await dialog_manager.switch_to(FlowMenu.schedule)

async def schedule_post(callback: CallbackQuery, widget, manager: DialogManager, selected_date):
    await callback.answer(f"Заплановано на {selected_date.strftime('%d.%m.%Y')}")
    await manager.switch_to(FlowMenu.posts_list)
