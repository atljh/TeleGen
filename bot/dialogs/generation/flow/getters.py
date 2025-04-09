
import logging
from pathlib import Path
from urllib.parse import urljoin
from aiogram_dialog import DialogManager
from aiogram.types import URLInputFile, InputMediaPhoto
from aiogram.enums import ContentType
from aiogram.types import InputFile
from aiogram.types import FSInputFile
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from django.conf import settings
import requests

from bot.containers import Container

from aiogram_dialog.api.entities import MediaAttachment, MediaId

from typing import Any, Dict
import os
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import StubScroll

from bot.database.dtos.dtos import MediaType

async def paging_getter(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    scroll: StubScroll = dialog_manager.find("stub_scroll")
    current_page = await scroll.get_page()

    start_data = dialog_manager.start_data or {}
    dialog_data = dialog_manager.dialog_data or {}

    channel = start_data.get("selected_channel") or dialog_data.get("selected_channel")
    flow = start_data.get("channel_flow") or dialog_data.get("channel_flow")

    if flow and "all_posts" not in dialog_data:
        post_service = Container.post_service()
        raw_posts = await post_service.get_posts_by_flow_id(flow.id)
        posts = []

        for idx, post in enumerate(raw_posts):
            pub_time = post.publication_date.strftime("%d.%m.%Y %H:%M") if post.publication_date else "Без дати"

            relative_path = post.media_url.lstrip("/")
            media_path = os.path.join(settings.BASE_DIR, relative_path) if post.media_url else None
            media = None
            if media_path and post.media_type:
                if post.media_type == MediaType.IMAGE:
                    media = MediaAttachment(
                        path=media_path,
                        type="photo"
                    )
                elif post.media_type == MediaType.VIDEO:
                    media = MediaAttachment(
                        path=media_path,
                        type="video"
                    )
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

    if not posts or current_page >= total_pages:
        return {
            "current_page": current_page + 1,
            "pages": total_pages,
            "day": "Немає поста",
        }

    post = posts[current_page]

    return {
        "current_page": current_page + 1,
        "pages": total_pages,
        "day": f"День {current_page + 1}",
        "media_content": post["media_path"],
        "post": post,
    }