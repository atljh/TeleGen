import os
import tempfile
import asyncio
import logging
from typing import Optional, List, Dict, AsyncGenerator
from contextlib import asynccontextmanager
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

class UserbotService:
    def __init__(self, api_id: int, api_hash: str, phone: str = None, 
                 session_path: str = "app/sessions/userbot.session"):
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
        try:
            await client.connect()
            if not await client.is_user_authorized():
                await client.start(phone=self.phone)
            yield client
        finally:
            await client.disconnect()

    async def get_last_posts(self, sources: List[Dict], limit: int = 10) -> List[Dict]:
        result = []
        async with self.get_client() as client:
            for source in sources:
                if len(result) >= limit:
                    break
                    
                if source['type'] != 'telegram':
                    continue

                try:
                    remaining_limit = limit - len(result)
                    entity = await client.get_entity(source['link'])
                    messages = await client.get_messages(entity, limit=remaining_limit)

                    for msg in messages:
                        post_data = await self._process_message(client, msg)
                        if post_data:
                            result.append(post_data)
                            if len(result) >= limit:
                                break

                except Exception as e:
                    logging.error(f"Error processing source {source['link']}: {str(e)}")
                    continue

        return result[::-1]

    async def _process_message(self, client: TelegramClient, msg) -> Optional[Dict]:
        if not msg.text and not msg.media:
            return None

        post_data = {
            'text': msg.text or '',
            'media': []
        }

        if msg.media:
            media_items = await self._extract_media(client, msg.media)
            post_data['media'].extend(media_items)

        return post_data

    async def _extract_media(self, client: TelegramClient, media) -> List[Dict]:
        media_items = []
        
        if hasattr(media, 'photo'):
            media_path = await self._download_media_file(client, media.photo, 'image')
            if media_path:
                media_items.append({
                    'type': 'image',
                    'path': media_path,
                    'file_id': getattr(media.photo, 'id', None)
                })
        
        elif hasattr(media, 'document'):
            if media.document.mime_type.startswith('video/'):
                media_path = await self._download_media_file(client, media.document, 'video')
                if media_path:
                    media_items.append({
                        'type': 'video',
                        'path': media_path,
                        'file_id': media.document.id
                    })
        
        return media_items

    async def _download_media_file(self, client: TelegramClient, media, media_type: str) -> Optional[str]:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{media_type}') as tmp_file:
                tmp_path = tmp_file.name
            
            await client.download_media(media, file=tmp_path)
            
            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                return tmp_path
            
            os.unlink(tmp_path)
            return None
            
        except Exception as e:
            logging.error(f"Media download failed: {str(e)}")
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return None