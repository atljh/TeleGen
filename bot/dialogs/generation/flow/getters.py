
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

async def selected_channel_getter(dialog_manager: DialogManager, **kwargs):
    start_data = dialog_manager.start_data or {}
    dialog_data = dialog_manager.dialog_data or {}
    
    channel = start_data.get("selected_channel") or dialog_data.get("selected_channel")
    flow = start_data.get("channel_flow") or dialog_data.get("channel_flow")
    posts = []

    if flow:
        post_service = Container.post_service()
        raw_posts = await post_service.get_posts_by_flow_id(flow.id)
        for idx, post in enumerate(raw_posts):
            pub_time = post.publication_date.strftime("%d.%m.%Y %H:%M") if post.publication_date else "Без дати"
            
            media = MediaAttachment(
                        path=post.media_path,
                        type="photo"
                    ),

            posts.append({
                "id": str(post.id),
                "idx": idx,
                "content_preview": (post.content[:100] + "...") if len(post.content) > 100 else post.content,
                "pub_time": pub_time,
                "status": "✅ Опубліковано" if post.is_published else "📝 Чернетка",
                "full_content": post.content,
                "media": media,
                "has_media": bool(media)
            })
    
    dialog_manager.dialog_data["all_posts"] = posts
    dialog_manager.dialog_data["total_posts"] = len(posts)
    
    return {
        "channel_name": channel.name if channel else "Канал не обрано",
        "channel_id": getattr(channel, "channel_id", "N/A"),
        "channel_flow": flow.name if flow else "Немає флоу",
        "posts_count": len(posts)
    }


async def get_current_post_data(dialog_manager: DialogManager, **kwargs):
    posts = dialog_manager.dialog_data.get("all_posts", [])
    scroll = dialog_manager.find("post_scroll")
    current_idx = await scroll.get_page()
    
    if not posts or current_idx >= len(posts):
        return {
            "current_post": {
                "content_preview": "Немає постів",
                "pub_time": "",
                "status": "",
                "full_content": "",
                "has_media": False
            },
            "post_number": 0,
            "posts_count": 0
        }
    
    current_post = posts[current_idx]
    return {
        "current_post": current_post,
        "post_number": current_idx + 1,
        "posts_count": len(posts),
        "media_content": current_post["media"] if current_post["has_media"] else None
    }