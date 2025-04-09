import logging
from typing import Dict, Any
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from datetime import datetime
import os
from django.conf import settings

EXAMPLE_POSTS = [
    {
        "image_path": "media/posts/images/photo_2025-04-02_17-44-44_wniiWc5.jpg",
        "content_preview": "Первый пост",
        "pub_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "🕒 В черновике",
    },
    {
        "image_path": "media/posts/images/Screenshot_2025-04-02_at_15.43.25.png",
        "content_preview": "Второй пост",
        "pub_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "✅ Опубликовано",
    },
    {
        "image_path": "media/posts/images/photo_2025-04-02_17-44-44_wniiWc5.jpg",
        "content_preview": "Третий пост",
        "pub_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "🕒 В черновике",
    },
]

async def paging_getter(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    scroll = dialog_manager.find("stub_scroll")
    current_page = await scroll.get_page()
    posts = EXAMPLE_POSTS
    total_pages = len(posts)

    post = posts[current_page]
    media_path = os.path.join(settings.BASE_DIR, post["image_path"])
    
    logging.info(post["image_path"])
    logging.info(media_path)
    return {
        "current_page": current_page + 1,
        "pages": total_pages,
        "day": f"День {current_page + 1}",
        "media": MediaAttachment(
            path=media_path,
            type="photo"
        ),
        "post": post
    }