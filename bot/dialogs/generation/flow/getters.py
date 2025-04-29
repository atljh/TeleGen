import os
import logging
from typing import Dict, Any, Optional

from aiogram.types import (
    InputMediaPhoto, FSInputFile, Message,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import StubScroll

from django.conf import settings
from asgiref.sync import sync_to_async
from functools import lru_cache

from bot.containers import Container


@lru_cache(maxsize=100)
def get_media_path(media_url: str) -> str:
    return os.path.join(settings.MEDIA_ROOT, media_url.split('/media/')[-1])

async def send_media_album(
    dialog_manager: DialogManager, 
    post_data: Dict[str, Any]
) -> Optional[Message]:
    bot = dialog_manager.middleware_data['bot']
    chat_id = dialog_manager.middleware_data['event_chat'].id
    message = dialog_manager.event.message
    
    try:
        images = post_data.get('images', [])[:10]
        if not images:
            return None
            
        media_group = []
        for i, image in enumerate(images):
            media_path = get_media_path(image.url)
            if not os.path.exists(media_path):
                continue
                
            media = InputMediaPhoto(
                media=FSInputFile(media_path),
                caption=post_data['content'] if i == 0 else None,
                parse_mode='HTML'
            )
            media_group.append(media)
        
        if media_group:
            try:
                await message.delete()
            except:
                pass
                
            new_messages = await bot.send_media_group(
                chat_id=chat_id,
                media=media_group
            )
            message_ids = [msg.message_id for msg in new_messages]

            # new_message = await bot.send_message(
            #     chat_id=chat_id,
            #     text=f"📷 Альбом ({len(images)} фото)\nУправление:",
            #     reply_markup=build_album_keyboard(post_data)
            # )
            
            dialog_manager.dialog_data["message_ids"] = message_ids
            
    except Exception as e:
        logging.error(f"Error sending media album: {str(e)}")
        await dialog_manager.event.answer("⚠️ Не вдалось вiдправити альбом")
    
    return None

def build_album_keyboard(post_data: dict) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Опублікувати", callback_data=f"publish_{post_data['id']}"),
            InlineKeyboardButton(text="✏️ Редагувати", callback_data=f"edit_{post_data['id']}"),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="go_back"),
        ]
    ])
    return keyboard

async def paging_getter(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    scroll: StubScroll = dialog_manager.find("stub_scroll")
    current_page = await scroll.get_page() if scroll else 0
    dialog_data = dialog_manager.dialog_data or {}
    start_data = dialog_manager.start_data or {}


    flow = start_data.get("channel_flow") or dialog_data.get("channel_flow")

    data = {
        "current_page": 1,
        "pages": 0,
        "day": "Немає постів",
        "media_content": None,
        "post": {
            "id": "",
            "idx": 0,
            "content_preview": "Тут будуть відображатися пости",
            "pub_time": "",
            "created_time": "",
            "status": "",
            "full_content": "",
            "has_media": False,
            "images_count": 0,
            "is_album": False
        }
    }

    if flow and "all_posts" not in dialog_data:
        post_service = Container.post_service()
        try:
            raw_posts = await post_service.get_posts_by_flow_id(flow.id)
            posts = []
            
            for idx, post in enumerate(raw_posts):
                images = post.images if hasattr(post, 'images') else []
                video_url = post.video_url if hasattr(post, 'video_url') else None
                content = post.content if hasattr(post, 'content') else ''
                
                pub_time = await sync_to_async(
                    lambda: post.publication_date.strftime("%d.%m.%Y %H:%M") 
                    if hasattr(post, 'publication_date') and post.publication_date 
                    else "Без дати"
                )()
                created_time = await sync_to_async(
                    lambda: post.created_at.strftime("%d.%m.%Y %H:%M") 
                    if hasattr(post, 'created_at') and post.created_at 
                    else "Без дати"
                )()

                is_album = len(images) > 1
                post_dict = {
                    "id": str(post.id) if hasattr(post, 'id') else "",
                    "idx": idx,
                    "content": content,
                    "pub_time": pub_time,
                    "created_time": created_time,
                    "status": "✅ Опубліковано" if getattr(post, 'is_published', False) else "📝 Чернетка",
                    "full_content": content,
                    "has_media": bool(images or video_url),
                    "images_count": len(images),
                    "images": images,
                    "video_url": video_url,
                    "is_album": is_album
                }

                if is_album:
                    post_dict["content_preview"] = f"📷 Альбом ({len(images)} фото)"
                else:
                    post_dict["content_preview"] = content[:1000] + ("..." if len(content) > 1000 else "")

                posts.append(post_dict)

            dialog_data["all_posts"] = posts
            dialog_data["total_posts"] = len(posts)

        except Exception as e:
            logging.error(f"Помилка завантаження постів: {str(e)}")

    posts = dialog_data.get("all_posts", [])
    total_pages = len(posts)

    if posts and current_page < total_pages:
        post = posts[current_page]
        data.update({
            "current_page": current_page + 1,
            "pages": total_pages,
            "day": f"День {current_page + 1}",
            "post": post
        })

        messages = dialog_manager.dialog_data.get("message_ids")
        if messages and not post.get('is_album'):
            for message_id in messages:
                bot = dialog_manager.middleware_data['bot']
                chat_id = dialog_manager.middleware_data['event_chat'].id
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
                dialog_manager.dialog_data["message_ids"] = []

        if not post.get('is_album'):
            media_info = None
            images = post.get('images', [])
            
            if images and len(images) == 1:
                first_image = images[0]
                if hasattr(first_image, 'url'):
                    media_info = {
                        'type': 'photo',
                        'url': first_image.url,
                        'path': get_media_path(first_image.url) if first_image.url else None
                    }
            elif post.get('video_url'):
                media_info = {
                    'type': 'video',
                    'url': post['video_url'],
                    'path': get_media_path(post['video_url'])
                }
            
            if media_info and media_info.get('path') and os.path.exists(media_info['path']):
                data["media_content"] = MediaAttachment(
                    path=media_info['path'],
                    type=media_info['type']
                )

    return data