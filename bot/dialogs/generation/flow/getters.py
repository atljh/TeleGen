import logging
import os
from datetime import datetime
from typing import Any

import pytz
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import StubScroll
from asgiref.sync import sync_to_async
from django.utils import timezone

from bot.containers import Container
from bot.database.models import PostStatus

from .utils import get_media_path, safe_delete_messages, send_media_album

logger = logging.getLogger(__name__)


def build_album_keyboard(post_data: dict[str, Any]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Опублікувати", callback_data=f"publish_{post_data['id']}"
                ),
                InlineKeyboardButton(
                    text="✏️ Редагувати", callback_data=f"edit_{post_data['id']}"
                ),
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="go_back")],
        ]
    )


def ensure_list(obj) -> list:
    if obj is None:
        return []
    if isinstance(obj, list | tuple):
        return list(obj)
    try:
        return list(obj.all())
    except Exception:
        try:
            return list(obj)
        except Exception:
            return []


def format_post_datetime(dt: datetime | None) -> str:
    if not dt:
        return "Без дати"
    try:
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return str(dt)


def build_post_dict(post: Any, idx: int) -> dict[str, Any]:
    images = ensure_list(getattr(post, "images", []))
    videos = getattr(post, "videos", getattr(post, "videos", None))
    content = getattr(post, "content", "") or ""
    original_link = getattr(post, "original_link", "") or ""
    original_date = getattr(post, "original_date", "") or ""
    source_url = getattr(post, "source_url", "") or ""

    pub_time = format_post_datetime(getattr(post, "publication_date", None))
    created_time = format_post_datetime(getattr(post, "created_at", None))

    post_stats = {
        PostStatus.DRAFT: "Чернетка",
        PostStatus.SCHEDULED: "Заплановано",
        PostStatus.PUBLISHED: "Опублiковано",
    }

    is_album = len(images) + len(videos) > 1
    images_count = len(images) + len(videos)

    post_dict = {
        "id": str(getattr(post, "id", "")),
        "idx": idx,
        "content": content,
        "pub_time": pub_time,
        "created_time": created_time,
        "status": post_stats.get(getattr(post, "status", PostStatus.DRAFT), ""),
        "full_content": content,
        "has_media": bool(images or videos),
        "images_count": images_count,
        "images": images,
        "videos": videos,
        "is_album": is_album,
        "original_date": original_date,
        "original_link": original_link,
        "source_url": source_url,
        "content_preview": f"📷 Альбом ({images_count} фото)"
        if is_album
        else (content[:1024] if content else "Тут будуть відображатися пости"),
    }

    return post_dict


async def load_raw_posts(flow_id: int, status: PostStatus) -> list[Any]:
    post_service = Container.post_service()
    raw_posts = await post_service.get_all_posts_in_flow(flow_id, status=status)
    if not isinstance(raw_posts, list | tuple):
        try:
            raw_posts = await sync_to_async(list)(raw_posts)
        except Exception:
            raw_posts = list(raw_posts)

    return raw_posts


async def build_posts_list(flow_id: int, status: PostStatus) -> list[dict[str, Any]]:
    raw_posts = await load_raw_posts(flow_id, status)
    posts: list[dict[str, Any]] = []

    for idx, post in enumerate(raw_posts):
        try:
            post_dict = build_post_dict(post, idx=idx)
            posts.append(post_dict)
        except Exception as e:
            logger.error(
                "Failed to build post dict for post id=%s: %s",
                getattr(post, "id", None),
                e,
                exc_info=True,
            )
            continue

    return posts


async def paging_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    scroll: StubScroll = dialog_manager.find("stub_scroll")
    current_page = await scroll.get_page() if scroll else 0

    dialog_data = dialog_manager.dialog_data or {}
    start_data = dialog_manager.start_data or {}
    flow = start_data.get("channel_flow") or dialog_data.get("channel_flow")

    dialog_manager.dialog_data["channel_flow"] = start_data.get("channel_flow")
    dialog_manager.dialog_data["selected_channel"] = start_data.get("selected_channel")

    data: dict[str, Any] = {
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
            "is_album": False,
        },
    }

    if dialog_data.pop("needs_refresh", False) or "all_posts" not in dialog_data:
        try:
            posts = await build_posts_list(flow.id, status=PostStatus.DRAFT)
            dialog_manager.dialog_data["all_posts"] = posts
            dialog_manager.dialog_data["total_posts"] = len(posts)
        except Exception as e:
            logger.error("Помилка завантаження постів: %s", e, exc_info=True)
            return data

    posts = dialog_manager.dialog_data.get("all_posts", [])
    total_pages = len(posts)

    dialog_manager.dialog_data["current_page"] = current_page

    if posts and current_page < total_pages:
        post = posts[current_page]
        data.update(
            {
                "current_page": current_page + 1,
                "pages": total_pages,
                "day": f"День {current_page + 1}",
                "post": post,
            }
        )

        messages = dialog_manager.dialog_data.get("message_ids", [])
        if messages and not post.get("is_album"):
            bot = dialog_manager.middleware_data["bot"]
            chat_id = dialog_manager.middleware_data["event_chat"].id
            await safe_delete_messages(bot, chat_id, messages)
            dialog_manager.dialog_data["message_ids"] = []

        if data["post"].get("is_album"):
            await send_media_album(dialog_manager, data["post"])
            return data

        if not post.get("is_album"):
            media_info: dict[str, Any] | None = None
            images = post.get("images", [])
            videos = post.get("videos", [])

            if images and len(images) == 1:
                first_image = images[0]
                image_url = getattr(first_image, "url", None)
                if image_url:
                    media_info = {
                        "type": "photo",
                        "url": image_url,
                        "path": get_media_path(image_url),
                    }
            if videos and len(videos) == 1:
                first_video = videos[0]
                video_url = getattr(first_video, "url", None)
                if video_url:
                    media_info = {
                        "type": "video",
                        "url": video_url,
                        "path": get_media_path(video_url),
                    }
            if (
                media_info
                and media_info.get("path")
                and os.path.exists(media_info["path"])
            ):
                data["media_content"] = MediaAttachment(
                    path=media_info["path"], type=media_info["type"]
                )

    return data


async def edit_post_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    post = dialog_manager.dialog_data.get("editing_post", {}) or {}
    content = dialog_manager.dialog_data.get("edited_content", post.get("content", ""))
    edited_media = dialog_manager.dialog_data.get("edited_media")
    media_info = None

    images = post.get("images", [])
    videos = post.get("videos", [])

    if images and len(images) == 1:
        first_image = images[0]
        image_url = getattr(first_image, "url", None)
        if image_url:
            media_info = {
                "type": "photo",
                "url": image_url,
                "path": get_media_path(image_url),
            }
    if videos and len(videos) == 1:
        first_video = videos[0]
        video_url = getattr(first_video, "url", None)
        if video_url:
            media_info = {
                "type": "video",
                "url": video_url,
                "path": get_media_path(video_url),
            }

    media: MediaAttachment | None = None
    if media_info and media_info.get("path") and os.path.exists(media_info["path"]):
        media = MediaAttachment(path=media_info["path"], type=media_info["type"])
    elif edited_media:
        media_path = get_media_path(edited_media["url"])
        media = MediaAttachment(path=media_path, type=edited_media["type"])

    return {"post": post, "content": content, "media": media}


async def post_info_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    dialog_data = await paging_getter(dialog_manager)
    post = dialog_data["post"]

    original_date = post.get("original_date", "")
    kiev_date = ""

    if original_date:
        try:
            if isinstance(original_date, str):
                dt = timezone.datetime.fromisoformat(original_date)
                if not timezone.is_aware(dt):
                    dt = timezone.make_aware(dt, timezone.utc)
            elif isinstance(original_date, datetime) and not timezone.is_aware(
                original_date
            ):
                dt = timezone.make_aware(original_date, timezone.utc)
            elif isinstance(original_date, datetime):
                dt = original_date
            else:
                raise ValueError("Unsupported date format")

            kiev_tz = pytz.timezone("Europe/Kiev")
            kiev_date = timezone.localtime(dt, timezone=kiev_tz).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        except Exception as e:
            logger.debug("Error converting date: %s", e, exc_info=True)
            kiev_date = original_date

    return {
        "status": post.get("status", ""),
        "source_url": post.get("source_url", ""),
        "original_link": post.get("original_link", ""),
        "original_date": kiev_date or original_date,
    }
