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
    def __init__(self, api_id: int, api_hash: str, phone: str = None, session_dir: str = "sessions"):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.session_dir = session_dir
        self.client = None
        self.lock = asyncio.Lock()
        os.makedirs(self.session_dir, exist_ok=True)

    async def initialize(self):
        async with self.lock:
            if self.client and self.client.is_connected():
                return

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
                auto_reconnect=True
            )
            
            try:
                await self.client.connect()
                
                if not await self.client.is_user_authorized():
                    logging.info("Starting authorization...")
                    if self.phone:
                        await self.client.start(phone=self.phone)
                    else:
                        raise ValueError("Phone number required")
                        
                logging.info("Telegram client ready")
            except Exception as e:
                logging.error(f"Initialization failed: {str(e)}")
                await self.disconnect()
                raise

    async def disconnect(self):
        async with self.lock:
            if self.client and self.client.is_connected():
                await self.client.disconnect()
            self.client = None

    async def _ensure_client(self):
        if not self.client or not self.client.is_connected():
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
                        'media_url': None,
                        'media_type': None
                    }
                    
                    if hasattr(msg, 'photo'):
                        tmp_path = await self.download_telegram_media(msg.photo, 'image')
                        if tmp_path:
                            post_data.update({
                                'media_url': tmp_path,
                                'media_type': 'image'
                            })
                    elif hasattr(msg, 'video'):
                        tmp_path = await self.download_telegram_media(msg.video, 'video')
                        if tmp_path:
                            post_data.update({
                                'media_url': tmp_path,
                                'media_type': 'video'
                            })
                    
                    result.append(post_data)
                    
            except Exception as e:
                logging.error(f"Error processing source {source['link']}: {str(e)}")
        
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
