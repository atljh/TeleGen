import os
import logging
import aiohttp
import asyncio
from typing import Any, Dict, Optional, List
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment
from aiogram.types import InputMediaPhoto, InputMediaVideo, Message, FSInputFile
from aiogram_dialog.widgets.kbd import StubScroll
from django.conf import settings
from bot.containers import Container
from asgiref.sync import sync_to_async
from functools import lru_cache


MAX_ALBUM_SIZE = 10
MAX_CAPTION_LENGTH = 1024

@lru_cache(maxsize=100)
def get_media_path(media_url: str) -> str:
    return os.path.join(settings.MEDIA_ROOT, media_url.split('/media/')[-1])

async def prepare_media_attachment(media_info: dict) -> Optional[MediaAttachment]:
    if not media_info or not os.path.exists(media_info['path']):
        return None
    return MediaAttachment(path=media_info['path'], type=media_info['type'])

async def send_media_album(
    dialog_manager: DialogManager, 
    post_data: Dict[str, Any]
) -> Optional[Message]:
    bot = dialog_manager.middleware_data['bot']
    chat_id = dialog_manager.middleware_data['event_chat'].id
    media_group = []
    
    try:
        images = post_data.get('images', [])[:MAX_ALBUM_SIZE]
        for i, image in enumerate(images):
            media_path = get_media_path(image.url)
            
            if not os.path.exists(media_path):
                continue
                
            media = InputMediaPhoto(
                media=FSInputFile(media_path),
                caption=post_data['content_preview'][:MAX_CAPTION_LENGTH] if i == 0 else None,
                parse_mode='HTML'
            )
            media_group.append(media)
        
        if not media_group and post_data.get('video_url'):
            video_path = get_media_path(post_data['video_url'])
            if os.path.exists(video_path):
                media_group.append(InputMediaVideo(
                    media=FSInputFile(video_path),
                    caption=post_data['content_preview'][:MAX_CAPTION_LENGTH],
                    parse_mode='HTML'
                ))
    
        if media_group:
            return await bot.send_media_group(
                chat_id=chat_id,
                media=media_group
            )
            
    except Exception as e:
        logging.error(f"Error sending media album: {str(e)}")
        await dialog_manager.event.answer("⚠️ Не удалось отправить альбом")
    
    return None

async def paging_getter(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    scroll: StubScroll = dialog_manager.find("stub_scroll")
    current_page = await scroll.get_page() if scroll else 0
    dialog_data = dialog_manager.dialog_data or {}
    start_data = dialog_manager.start_data or {}

    flow = start_data.get("channel_flow") or dialog_data.get("channel_flow")

    # Базова структура даних
    data = {
        "current_page": 1,
        "pages": 0,
        "day": "Немає постів",
        "media_content": None,
        "auto_sent_album": False,
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
        }
    }

    if flow and "all_posts" not in dialog_data:
        post_service = Container.post_service()
        try:
            raw_posts = await post_service.get_posts_by_flow_id(flow.id)
            posts = []
            
            for idx, post in enumerate(raw_posts):
                # Безпечне отримання даних через атрибути DTO
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
                }

                # Формуємо прев'ю
                if len(images) > 1:
                    post_dict["content_preview"] = f"📷 Альбом ({len(images)} фото)\n{content[:300]}..."
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
        
        if post.get('images_count', 0) > 1:
            try:
                await send_media_album(dialog_manager, post)
                data["auto_sent_album"] = True
            except Exception as e:
                logging.error(f"Помилка відправки альбому: {str(e)}")
                data["auto_sent_album"] = False

        data.update({
            "current_page": current_page + 1,
            "pages": total_pages,
            "day": f"День {current_page + 1}",
            "post": post
        })

        if post.get('images_count', 0) <= 1:
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