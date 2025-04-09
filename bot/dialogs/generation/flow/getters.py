import os
import logging
from urllib.parse import unquote
from pathlib import Path
from typing import Any, Dict
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.kbd import StubScroll
from django.conf import settings
from bot.containers import Container
from bot.database.dtos.dtos import MediaType

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
            "status": "",
            "full_content": "",
            "media_path": None,
        }
    }

    if flow and "all_posts" not in dialog_data:
        post_service = Container.post_service()
        raw_posts = await post_service.get_posts_by_flow_id(flow.id)
        posts = []

        for idx, post in enumerate(raw_posts):
            pub_time = post.publication_date.strftime("%d.%m.%Y %H:%M") if post.publication_date else "Без дати"

            relative_path = post.media_url.lstrip("/") if post.media_url else None
            media_path = os.path.join(settings.BASE_DIR, relative_path) if relative_path else None
            media = None

            if media_path and post.media_type:
                try:
                    if post.media_type == MediaType.IMAGE:
                        media = MediaAttachment(
                            path=media_path,
                            type="photo"
                        )
                    elif post.media_type == MediaType.VIDEO:
                        decoded_path = unquote(post.media_url)
                        relative_path = decoded_path.lstrip("/")
                        media_path = os.path.join(settings.BASE_DIR, relative_path)
                        media = MediaAttachment(
                            path=media_path,
                            type="video"
                        )
                except Exception as e:
                    logging.error(f"Error creating media attachment: {e}")

            posts.append({
                "id": str(post.id),
                "idx": idx,
                "content_preview": (post.content[:100] + "...") if len(post.content) > 100 else post.content,
                "pub_time": pub_time,
                "status": "✅ Опубліковано" if post.is_published else "📝 Чернетка",
                "full_content": post.content,
                "media_path": media,
            })

        dialog_manager.dialog_data["all_posts"] = posts
        dialog_manager.dialog_data["total_posts"] = len(posts)

    posts = dialog_manager.dialog_data.get("all_posts", [])
    total_pages = len(posts)

    if posts and current_page < total_pages:
        post = posts[current_page]
        data = {
            "current_page": current_page + 1,
            "pages": total_pages,
            "day": f"День {current_page + 1}",
            "media_content": post.get("media_path"),
            "post": {
                "id": post.get("id", ""),
                "idx": post.get("idx", 0),
                "content_preview": post.get("content_preview", ""),
                "pub_time": post.get("pub_time", ""),
                "status": post.get("status", ""),
                "full_content": post.get("full_content", ""),
                "media_path": post.get("media_path"),
            }
        }

    return data