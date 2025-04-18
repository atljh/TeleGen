import os
import uuid
import asyncio
import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from django.conf import settings
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto
from tempfile import NamedTemporaryFile


class UserbotService:
    def __init__(self, api_id: int, api_hash: str, phone: str = None, session_path: str = "app/sessions/userbot.session"):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.session_path = session_path
        os.makedirs(os.path.dirname(self.session_path), exist_ok=True)

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[TelegramClient, None]:
        client = TelegramClient(
            session=self.session_path,
            api_id=self.api_id,
            api_hash=self.api_hash,
            connection_retries=5,
            auto_reconnect=True,
        )
        client._loop = asyncio.get_event_loop()
        try:
            await client.connect()
            if not await client.is_user_authorized():
                await client.start(phone=self.phone)
            yield client
        except Exception as e:
            logging.error(f"Failed to connect/start client: {e}")
            raise
        finally:
            await client.disconnect()

    async def get_last_posts_with_media(self, sources: list[dict], limit: int = 10) -> list[dict]:
        result = []
        async with self.get_client() as client:
            for source in sources:
                if source['type'] != 'telegram':
                    continue

                try:
                    entity = await client.get_entity(source['link'])
                    messages = await client.get_messages(entity, limit=limit)

                    for msg in messages:
                        post_data = {
                            'text': msg.text or '',
                            'media': []
                        }

                        if msg.media:
                            if hasattr(msg.media, 'photo'):
                                media_path = await self.download_telegram_media(client, msg.media.photo, 'image')
                                if media_path:
                                    post_data['media'].append({
                                        'type': 'image',
                                        'path': media_path
                                    })
                            elif hasattr(msg.media, 'document'):
                                if msg.media.document.mime_type.startswith('video/'):
                                    media_path = await self.download_telegram_media(client, msg.media.document, 'video')
                                    if media_path:
                                        post_data['media'].append({
                                            'type': 'video',
                                            'path': media_path
                                        })

                        if post_data['text'] or post_data['media']:
                            result.append(post_data)

                except Exception as e:
                    logging.error(f"Error processing source {source['link']}: {str(e)}")
                    continue

        return result

    async def download_telegram_media(self, client: TelegramClient, media, media_type: str) -> Optional[str]:
        try:
            ext = '.jpg' if media_type == 'image' else '.mp4'
            with NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp_path = tmp.name

            await client.download_media(media, file=tmp_path)

            if os.path.getsize(tmp_path) > 0:
                return tmp_path
            os.unlink(tmp_path)
            return None
        except Exception as e:
            logging.error(f"Error downloading Telegram media: {str(e)}")
            return None

    async def download_media_to_storage(self, media, media_type: str) -> Optional[str]:
        try:
            media_dir = 'posts/images' if media_type == 'image' else 'posts/videos'
            os.makedirs(os.path.join(settings.MEDIA_ROOT, media_dir), exist_ok=True)
            
            filename = f"{uuid.uuid4()}.{'jpg' if media_type == 'image' else 'mp4'}"
            storage_path = os.path.join(media_dir, filename)
            full_path = os.path.join(settings.MEDIA_ROOT, storage_path)
            
            await self.client.download_media(
                media,
                file=full_path
            )
            
            if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
                return storage_path
            
            return None
        except Exception as e:
            logging.error(f"Error downloading media: {str(e)}")
            return None