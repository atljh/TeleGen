import asyncio
import atexit
import logging
import os
import tempfile
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from telethon import TelegramClient

from admin_panel.admin_panel.models import Post
from bot.database.models import PostDTO

from .client_manager import TelegramClientManager


class BaseUserbotService:
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        phone: str = None,
        session_path: Optional[str] = None,
    ):
        self.phone = phone
        self.download_semaphore = asyncio.Semaphore(10)
        self._temp_files = set()
        self.logger = logging.getLogger(__name__)

        self.client_manager = TelegramClientManager(
            api_id=api_id, api_hash=api_hash, phone=phone, session_path=session_path
        )

    def cleanup_temp_files(self):
        for file_path in self._temp_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                self.logger.error(f"Error deleting temp file {file_path}: {str(e)}")
        self._temp_files.clear()

    async def get_last_posts(self, sources: List[Dict], limit: int = 10) -> List[Dict]:
        telegram_sources = [s for s in sources if s.get("type") == "telegram"]
        if not telegram_sources:
            return []

        result = []
        processed_albums = set()
        source_limits = self._calculate_source_limits(sources, limit)
        total_posts_needed = limit

        async with self.client_manager.get_client() as client:
            for source in telegram_sources:
                if source["type"] != "telegram":
                    continue

                if len(result) >= total_posts_needed:
                    break

                try:
                    remaining_for_source = source_limits[source["link"]]
                    if remaining_for_source <= 0:
                        continue

                    entity = await self.client_manager.get_entity(
                        client, source["link"]
                    )
                    if not entity:
                        continue

                    await self._process_source_messages(
                        client,
                        entity,
                        source,
                        remaining_for_source,
                        result,
                        processed_albums,
                        total_posts_needed,
                    )

                except Exception as e:
                    self.logger.error(
                        f"Error processing source {source['link']}: {str(e)}"
                    )
                    continue

        self.logger.info(f"Final result length: {len(result)}")
        return result[:total_posts_needed]

    async def _process_source_messages(
        self,
        client,
        entity,
        source,
        remaining_for_source,
        result,
        processed_albums,
        total_posts_needed,
    ):
        messages = await client.get_messages(entity, limit=remaining_for_source * 3)

        for msg in messages:
            if len(result) >= total_posts_needed:
                break

            if await self._contains_external_links(client, msg, entity):
                self.logger.info("Post contains external link. PASS")
                continue

            process_result = await self._process_message_or_album(
                client, entity, msg, source["link"], processed_albums
            )

            if process_result is None:
                continue

            post_data, post_count = process_result
            result.append(post_data)

            self.logger.info(
                f"Added {'album' if post_count > 1 else 'post'} "
                f"(size {post_count}). Result: {len(result)}/{total_posts_needed}"
            )

    async def _contains_external_links(self, client, message, channel_entity) -> bool:
        if not message.entities:
            return False

        channel_username = getattr(channel_entity, "username", None)
        channel_id = channel_entity.id

        # for entity in message.entities:
        # if isinstance(entity, MessageEntityTextUrl):
        #     url = entity.url
        #     if url.startswith('https://t.me/'):
        #         mentioned_username = url.split('/')[-1]
        #         if mentioned_username.lower() != channel_username.lower():
        #             return True

        # elif isinstance(entity, MessageEntityUrl):
        #     text = message.text[entity.offset:entity.offset+entity.length]
        #     if text.startswith('https://t.me/'):
        #         mentioned_username = text.split('/')[-1]
        #         if mentioned_username.lower() != channel_username.lower():
        #             return True

        if message.reply_markup:
            for row in message.reply_markup.rows:
                for button in row.buttons:
                    if hasattr(button, "url"):
                        url = button.url
                        if url.startswith("https://t.me/"):
                            mentioned_username = url.split("/")[-1]
                            if mentioned_username.lower() != channel_username.lower():
                                return True

        return False

    async def _process_message_or_album(
        self, client, entity, msg, source_link, processed_albums
    ) -> Tuple[Optional[Dict], int]:
        chat_id = msg.chat_id if hasattr(msg, "chat_id") else entity.id

        post_date = msg.date if hasattr(msg, "date") else None

        if post_date:
            last_post = (
                await Post.objects.filter(source_id__startswith=f"telegram_{chat_id}_")
                .order_by("-original_date")
                .afirst()
            )

            if (
                last_post
                and last_post.original_date
                and post_date <= last_post.original_date
            ):
                logging.info(
                    f"Skipping old post from {post_date} (last in DB: {last_post.original_date})"
                )
                return None, 0

        if hasattr(msg, "grouped_id") and msg.grouped_id:
            if msg.grouped_id in processed_albums:
                logging.info(f"Skipping already processed album {msg.grouped_id}")
                return None, 0

            source_id = f"telegram_{chat_id}_album_{msg.grouped_id}"

            if await Post.objects.filter(source_id=source_id).aexists():
                processed_albums.add(msg.grouped_id)
                logging.info(f"Album {msg.grouped_id} already exists in DB")
                return None, 0

            processed_albums.add(msg.grouped_id)
            post_data = await self._process_album(client, entity, msg, source_link)
            if not post_data:
                return None, 0

            album_size = post_data.get("album_size", 1)
            logging.info(f"Processed album {msg.grouped_id} with {album_size} messages")
            post_data["source_id"] = source_id
            return post_data, album_size
        else:
            source_id = f"telegram_{chat_id}_{msg.id}"

            if await Post.objects.filter(source_id=source_id).aexists():
                logging.info(f"Message {msg.id} already exists in DB")
                return None, 0

            post_data = await self._process_message(client, msg, source_link)
            if not post_data:
                return None, 0

            logging.info(f"Processed single message {msg.id}")
            post_data["source_id"] = source_id
            return post_data, 1

    def _calculate_source_limits(
        self, sources: List[Dict], limit: int
    ) -> Dict[str, int]:
        source_limits = {}
        base_limit = max(1, limit // len(sources))
        for source in sources:
            source_limits[source["link"]] = base_limit

        remaining = limit - base_limit * len(sources)
        for source in sources[:remaining]:
            source_limits[source["link"]] += 1

        return source_limits

    async def _process_album(
        self, client: TelegramClient, entity, initial_msg, source_url: str
    ) -> Optional[Dict]:
        try:
            messages = await client.get_messages(
                entity, min_id=initial_msg.id - 10, max_id=initial_msg.id + 10, limit=20
            )

            album_messages = [
                msg
                for msg in messages
                if hasattr(msg, "grouped_id")
                and msg.grouped_id == initial_msg.grouped_id
            ]

            if not album_messages:
                return None

            all_media = []
            texts = []
            for msg in album_messages:
                if msg.text:
                    texts.append(msg.text)
                if msg.media:
                    all_media.extend(await self._extract_media(client, msg.media))

            downloaded_media = (
                await self._download_media_batch(client, all_media) if all_media else []
            )

            original_link = f"https://t.me/c/{entity.id}/{initial_msg.id}"

            post_data = {
                "original_content": "\n\n".join(texts) if texts else "",
                "text": "\n\n".join(texts) if texts else "",
                "media": downloaded_media,
                "is_album": True,
                "album_size": len(album_messages),
                "original_link": original_link,
                "original_date": initial_msg.date,
                "source_url": source_url,
            }

            if not post_data["text"] and not post_data["media"]:
                return None

            return post_data

        except Exception as e:
            logging.error(f"Error processing album: {str(e)}")
            return None

    async def _process_message(
        self, client: TelegramClient, msg, source_url: str
    ) -> Optional[Dict]:
        if not msg.text and not msg.media:
            return None

        try:
            entity = await msg.get_chat()
            original_link = f"https://t.me/c/{entity.id}/{msg.id}"
        except Exception as e:
            logging.error(f"Could not generate original link: {str(e)}")
            original_link = None
        post_data = {
            "original_content": msg.text or "",
            "text": msg.text or "",
            "media": [],
            "is_album": False,
            "album_size": 0,
            "original_link": original_link,
            "original_date": msg.date,
            "source_url": source_url,
        }
        if msg.media:
            media_items = await self._extract_media(client, msg.media)
            post_data["media"] = await self._download_media_batch(client, media_items)

        return post_data

    async def _extract_media(self, client: TelegramClient, media) -> List[Dict]:
        media_items = []

        if hasattr(media, "photo"):
            media_items.append(
                {
                    "type": "image",
                    "media_obj": media.photo,
                    "file_id": getattr(media.photo, "id", None),
                }
            )
        elif hasattr(media, "document") and media.document.mime_type.startswith(
            "video/"
        ):
            media_items.append(
                {
                    "type": "video",
                    "media_obj": media.document,
                    "file_id": media.document.id,
                }
            )

        return media_items

    async def _download_media_batch(
        self, client: TelegramClient, media_items: List[Dict]
    ) -> List[Dict]:
        self.logger.info(f"Starting download of {len(media_items)} media files...")
        start_time = time.time()
        downloaded = 0

        async def _download_with_progress(item):
            nonlocal downloaded
            try:
                path = await self._download_media_file(
                    client, item["media_obj"], item["type"]
                )
                downloaded += 1
                progress = downloaded / len(media_items) * 100
                elapsed = time.time() - start_time
                self.logger.info(
                    f"Download progress: {downloaded}/{len(media_items)} "
                    f"({progress:.1f}%) | Elapsed: {elapsed:.1f}s"
                )
                return path
            except Exception as e:
                self.logger.error(f"Error downloading {item['type']}: {str(e)}")
                return e

        tasks = [_download_with_progress(item) for item in media_items]
        downloaded_paths = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            {**item, "path": path}
            for item, path in zip(media_items, downloaded_paths)
            if not isinstance(path, Exception) and path
        ]

    async def _download_media_file(
        self, client: TelegramClient, media, media_type: str
    ) -> Optional[str]:
        async with self.download_semaphore:
            try:
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=f".{media_type}"
                ) as tmp_file:
                    tmp_path = tmp_file.name
                    self._temp_files.add(tmp_path)

                await client.download_media(media, file=tmp_path)

                if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                    return tmp_path

                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    self._temp_files.discard(tmp_path)
                    return None

            except Exception as e:
                logging.error(f"Media download failed: {str(e)}")
                if "tmp_path" in locals() and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                        self._temp_files.discard(tmp_path)
                    except:
                        pass
                return None

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.cleanup_temp_files()

    def __del__(self):
        self.cleanup_temp_files()
