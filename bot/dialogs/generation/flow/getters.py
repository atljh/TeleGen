import os
import logging
import aiohttp
import asyncio
from typing import Any, Dict, Optional
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import StubScroll
from django.conf import settings
from bot.containers import Container
from asgiref.sync import sync_to_async
from functools import lru_cache

@lru_cache(maxsize=100)
def get_media_path(media_url: str) -> str:
    return os.path.join(settings.MEDIA_ROOT, media_url.split('/media/')[-1])

async def try_load_media(media_info: dict) -> Optional[MediaAttachment]:
    try:
        if not os.path.exists(media_info['path']):
            if media_info['url'].startswith(('http', 'https')):
                async with aiohttp.ClientSession() as session:
                    async with session.get(media_info['url']) as resp:
                        if resp.status == 200:
                            os.makedirs(os.path.dirname(media_info['path']), exist_ok=True)
                            with open(media_info['path'], 'wb') as f:
                                f.write(await resp.read())
                            logging.debug(f"Downloaded media: {media_info['path']}")
        
        if os.path.exists(media_info['path']):
            return MediaAttachment(
                path=media_info['path'],
                type=media_info['type']
            )
    except Exception as e:
        logging.debug(f"Media load failed: {str(e)}")
    return None

async def background_preload(posts: list, current_index: int):
    try:
        for i in range(current_index + 1, min(current_index + 4, len(posts))):
            post = posts[i]
            if post.get('media_info'):
                asyncio.create_task(try_load_media(post['media_info']))
    except Exception as e:
        logging.debug(f"Background preload error: {str(e)}")

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
                })

            dialog_data["all_posts"] = posts
            dialog_data["total_posts"] = len(posts)

        except Exception as e:
            logging.error(f"Error loading posts: {str(e)}")

    posts = dialog_data.get("all_posts", [])
    total_pages = len(posts)

    if posts and current_page < total_pages:
        post = posts[current_page]
        
        media = None
        if post.get('media_info'):
            media = await try_load_media(post['media_info'])

        await background_preload(posts, current_page)

        data = {
            "current_page": current_page + 1,
            "pages": total_pages,
            "day": f"День {current_page + 1}",
            "media_content": media,
            "post": {
                "id": post["id"],
                "idx": post["idx"],
                "content_preview": post["content_preview"],
                "pub_time": post["pub_time"],
                "created_time": post["created_time"],
                "status": post["status"],
                "full_content": post["full_content"],
                "has_media": post["has_media"],
                "images_count": post["images_count"],
            }
        }

    return data