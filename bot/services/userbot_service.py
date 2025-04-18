import os
import asyncio
import logging
from typing import Optional
import uuid
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto
from tempfile import NamedTemporaryFile

from bot.database.dtos import FlowDTO


class UserbotService:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, api_id: int, api_hash: str, phone: str = None, session_dir: str = "sessions"):
        if hasattr(self, 'client'):
            return
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.session_dir = session_dir
        self.client = None
        self.is_initialized = False
        os.makedirs(self.session_dir, exist_ok=True)


    async def initialize(self):
        async with self._lock:
            if self.is_initialized:
                return
        # async with self.lock:
        #     if self.client and self.client.is_connected():
        #         return

            session_path = "app/sessions/userbot.session"

            if os.path.exists(session_path):
                logging.info("Session file exists")
            else:
                logging.info("Session file doesnt exists")

            self.client = TelegramClient(
                session=session_path,
                api_id=self.api_id,
                api_hash=self.api_hash,
                connection_retries=5,
                auto_reconnect=True,
            )
            
            try:
                await self.client.connect()
                if not await self.client.is_user_authorized():
                    await self.client.start(phone=self.phone)
                self.is_initialized = True
            except Exception as e:
                await self.disconnect()
                raise


    async def disconnect(self):
        async with self._lock:
            if self.client and self.client.is_connected():
                await self.client.disconnect()
            self.client = None

    async def _ensure_client(self):
        if not self.client or not self.client.is_connected():
            await self.initialize()

    async def reconnect(self):
        async with self._lock:
            await self.disconnect()
            self.is_initialized = False
            await self.initialize()

    async def get_last_posts_with_media(self, sources: list[dict], limit: int = 10) -> list[dict]:
        await self._ensure_client()
        
        result = []
        for source in sources:
            if source['type'] != 'telegram':
                continue
                
            try:
                entity = await self.client.get_entity(source['link'])
                messages = await self.client.get_messages(entity, limit=limit)
                
                for msg in messages:
                    post_data = {
                        'text': msg.text or '',
                        'media': []
                    }
                    
                    if msg.media:
                        if hasattr(msg.media, 'photo'):
                            media_path = await self.download_telegram_media(msg.media.photo, 'image')
                            if media_path:
                                post_data['media'].append({
                                    'type': 'image',
                                    'path': media_path
                                })
                        elif hasattr(msg.media, 'document'):
                            if msg.media.document.mime_type.startswith('video/'):
                                media_path = await self.download_telegram_media(msg.media.document, 'video')
                                if media_path:
                                    post_data['media'].append({
                                        'type': 'video', 
                                        'path': media_path
                                    })
                    
                    if post_data['text'] or post_data['media']:
                        result.append(post_data)
                        
            except Exception as e:
                logging.error(f"Error processing source {source['link']}: {str(e)}")
                await self.reconnect()
                return await self.client.get_messages(entity, limit=limit)
        
        return result


    async def download_telegram_media(self, media, media_type: str) -> Optional[str]:
        try:
            ext = '.jpg' if media_type == 'image' else '.mp4'
            with NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp_path = tmp.name
            
            await self.client.download_media(
                media,
                file=tmp_path
            )
            
            if os.path.getsize(tmp_path) > 0:
                return tmp_path
            os.unlink(tmp_path)
            return None
        except Exception as e:
            logging.error(f"Error downloading Telegram media: {str(e)}")
            return None
