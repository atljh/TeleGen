import os
import logging
import aiohttp
import asyncio
from typing import Any, Dict, Optional, List
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment
from aiogram.types import InputMediaPhoto, InputMediaVideo, Message
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
                
            with open(media_path, 'rb') as file:
                media = InputMediaPhoto(
                    media=file,
                    caption=post_data['content'][:MAX_CAPTION_LENGTH] if i == 0 else None,
                    parse_mode='HTML'
                )
                media_group.append(media)
        
        if not media_group and post_data.get('video_url'):
            video_path = get_media_path(post_data['video_url'])
            if os.path.exists(video_path):
                with open(video_path, 'rb') as file:
                    media_group.append(InputMediaVideo(
                        media=file,
                        caption=post_data['content'][:MAX_CAPTION_LENGTH],
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

    data = {
        "current_page": 1,
        "pages": 0,
        "day": "Немає постів",
        "media_content": None,
        "show_album_btn": False,
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
                pub_time = await sync_to_async(
                    lambda: post.publication_date.strftime("%d.%m.%Y %H:%M") if post.publication_date else "Без дати"
                )()
                created_time = await sync_to_async(
                    lambda: post.created_at.strftime("%d.%m.%Y %H:%M") if post.created_at else "Без дати"
                )()

                media_info = None
                if post.images:
                    first_image = post.images[0]
                    media_info = {
                        'type': 'photo',
                        'url': first_image.url,
                        'path': get_media_path(first_image.url)
                    }
                elif post.video_url:
                    media_info = {
                        'type': 'video',
                        'url': post.video_url,
                        'path': get_media_path(post.video_url)
                    }

                posts.append({
                    "id": str(post.id),
                    "idx": idx,
                    "content_preview": (post.content[:1000] + "...") if len(post.content) > 1000 else post.content,
                    "pub_time": pub_time,
                    "created_time": created_time,
                    "status": "✅ Опубліковано" if post.is_published else "📝 Чернетка",
                    "full_content": post.content,
                    "media_info": media_info,
                    "has_media": bool(post.images or post.video_url),
                    "images_count": len(post.images),
                    "images": post.images,
                    "video_url": post.video_url,
                })

            dialog_data["all_posts"] = posts
            dialog_data["total_posts"] = len(posts)

        except Exception as e:
            logging.error(f"Error loading posts: {str(e)}")

    posts = dialog_data.get("all_posts", [])
    total_pages = len(posts)

    if posts and current_page < total_pages:
        post = posts[current_page]
        
        if post['images_count'] > 1:
            data.update({
                "current_page": current_page + 1,
                "pages": total_pages,
                "day": f"День {current_page + 1}",
                "show_album_btn": True,
                "post": {
                    **post,
                    "content_preview": f"📷 Альбом ({post['images_count']} фото)\n{post['content_preview'][:300]}...",
                }
            })
        else:
            media = await prepare_media_attachment(post.get('media_info'))
            data.update({
                "current_page": current_page + 1,
                "pages": total_pages,
                "day": f"День {current_page + 1}",
                "media_content": media,
                "post": post
            })

    return data