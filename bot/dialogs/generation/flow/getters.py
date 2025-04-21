import os
import logging
from urllib.parse import unquote
from typing import Any, Dict
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import StubScroll
from django.conf import settings
from bot.containers import Container
from bot.database.dtos.dtos import MediaType
from asgiref.sync import sync_to_async

async def paging_getter(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    scroll: StubScroll = dialog_manager.find("stub_scroll")
    current_page = await scroll.get_page() if scroll else 0


    start_data = dialog_manager.start_data or {}
    dialog_data = dialog_manager.dialog_data or {}

    channel = start_data.get("selected_channel") or dialog_data.get("selected_channel")
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
            "media_path": None,
        }
    }

    if flow and "all_posts" not in dialog_manager.dialog_data:
        post_service = Container.post_service()
        raw_posts = await post_service.get_posts_by_flow_id(flow.id)
        posts = []

        for idx, post in enumerate(raw_posts):
            pub_time = post.publication_date.strftime("%d.%m.%Y %H:%M") if post.publication_date else "Без дати"
            created_time = post.created_at.strftime("%d.%m.%Y %H:%M") if post.created_at else "Без дати"

            media = None
            if post.images:
                first_image = post.images[0]
                media = {
                    'type': 'photo',
                    'url': first_image,
                    'path': os.path.join(settings.MEDIA_ROOT, first_image.url.split('/media/')[-1])
                }
            elif post.video_url:
                media = {
                    'type': 'video', 
                    'url': post.video_url,
                    'path': os.path.join(settings.MEDIA_ROOT, post.video_url.split('/media/')[-1])
                }

            posts.append({
                "id": str(post.id),
                "idx": idx,
                "content_preview": (post.content[:1000] + "...") if len(post.content) > 1000 else post.content,
                "pub_time": pub_time,
                "created_time": created_time,
                "status": "✅ Опубліковано" if post.is_published else "📝 Чернетка",
                "full_content": post.content,
                "media_info": media,
                "has_media": bool(post.images or post.video_url),
                "images_count": len(post.images),
            })

        dialog_manager.dialog_data["all_posts"] = posts
        dialog_manager.dialog_data["total_posts"] = len(posts)

    posts = dialog_manager.dialog_data.get("all_posts", [])
    total_pages = len(posts)

    if posts and current_page < len(posts):
        post = posts[current_page]
        if post['media_info'] and os.path.exists(post['media_info']['path']):
            media = MediaAttachment(
                path=post['media_info']['path'],
                type=post['media_info']['type']
            )
        else:
            media = None
        
        data = {
            "current_page": current_page + 1,
            "pages": total_pages,
            "day": f"День {current_page + 1}",
            "media_content": media,
            "post": post
        }

    return data