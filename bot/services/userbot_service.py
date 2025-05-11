import os
import time
import asyncio
import logging
import tempfile
from datetime import datetime
from tqdm.asyncio import tqdm_asyncio
from typing import Optional, List, Dict, AsyncGenerator
from contextlib import asynccontextmanager
import openai
from telethon import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest

from bot.database.dtos.dtos import FlowDTO, PostDTO
from bot.services.content_processing.processors import ChatGPTContentProcessor, DefaultContentProcessor

from bot.services.aisettings_service import AISettingsService

class UserbotService:
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        aisettings_service: AISettingsService,
        phone: str = None,
        session_path: Optional[str] = None,
    ):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.session_path = session_path or os.getenv("SESSION_PATH", "userbot.session")
        self.download_semaphore = asyncio.Semaphore(10)
        self.aisettings_service = aisettings_service
        
        if not os.path.isabs(self.session_path):
            self.session_path = os.path.join('/app/sessions', self.session_path)
        
        os.makedirs(os.path.dirname(self.session_path), exist_ok=True)

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[TelegramClient, None]:
        client = TelegramClient(
            session=self.session_path,
            api_id=self.api_id,
            api_hash=self.api_hash,
            connection_retries=5,
            auto_reconnect=True,
            use_ipv6=False,
            proxy=None 
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
        processed_albums = set()

        async with self.get_client() as client:
            for source in sources:
                if len(result) >= limit:
                    break

                if source['type'] != 'telegram':
                    continue

                try:
                    remaining_limit = limit - len(result)
                    entity = None

                    try:
                        entity = await client.get_entity(source['link'])
                    except Exception as e:
                        if 't.me/+' in source['link']:
                            invite_hash = source['link'].split('+')[-1]
                            try:
                                await client(ImportChatInviteRequest(invite_hash))
                                entity = await client.get_entity(source['link'])
                            except Exception as join_err:
                                logging.error(f"Failed to join private chat {source['link']}: {join_err}")
                                continue
                            else:
                                logging.info(f"Joined private channel {source['link']}")
                        else:
                            logging.error(f"Failed to get entity for {source['link']}: {e}")
                            continue

                    messages = await client.get_messages(entity, limit=remaining_limit * 2)

                    for msg in messages:
                        if hasattr(msg, 'grouped_id') and msg.grouped_id in processed_albums:
                            continue

                        if hasattr(msg, 'grouped_id') and msg.grouped_id:
                            processed_albums.add(msg.grouped_id)
                            post_data = await self._process_album(client, entity, msg)
                        else:
                            post_data = await self._process_message(client, msg)
                        
                        if post_data:
                            result.append(post_data)
                            if len(result) >= limit:
                                break

                except Exception as e:
                    logging.error(f"Error processing source {source['link']}: {str(e)}")
                    continue

        return result[::-1]

    async def _process_album(self, client: TelegramClient, entity, initial_msg) -> Optional[Dict]:
        try:
            messages = await client.get_messages(
                entity,
                min_id=initial_msg.id - 10,
                max_id=initial_msg.id + 10,
                limit=20
            )
            
            album_messages = [
                msg for msg in messages
                if hasattr(msg, 'grouped_id') and msg.grouped_id == initial_msg.grouped_id
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
            
            downloaded_media = await self._download_media_batch(client, all_media)
            
            original_link = f"https://t.me/c/{entity.id}/{initial_msg.id}"
            
            post_data = {
                'text': "\n\n".join(texts) if texts else "",
                'media': downloaded_media,
                'is_album': True,
                'album_size': len(album_messages),
                'original_link': original_link,
                'original_date': initial_msg.date
            }
            return post_data
            
        except Exception as e:
            logging.error(f"Error processing album: {str(e)}")
            return None

    async def _process_message(self, client: TelegramClient, msg) -> Optional[Dict]:
        if not msg.text and not msg.media:
            return None
            
        try:
            entity = await msg.get_chat()
            original_link = f"https://t.me/c/{entity.id}/{msg.id}"
        except Exception as e:
            logging.error(f"Could not generate original link: {str(e)}")
            original_link = None

        post_data = {
            'text': msg.text or '',
            'media': [],
            'is_album': False,
            'album_size': 0,
            'original_link': original_link,
            'original_date': msg.date
        }

        if msg.media:
            media_items = await self._extract_media(client, msg.media)
            post_data['media'] = await self._download_media_batch(client, media_items)

        return post_data

    async def _extract_media(self, client: TelegramClient, media) -> List[Dict]:
        media_items = []
        
        if hasattr(media, 'photo'):
            media_items.append({
                'type': 'image',
                'media_obj': media.photo,
                'file_id': getattr(media.photo, 'id', None)
            })
        elif hasattr(media, 'document') and media.document.mime_type.startswith('video/'):
            media_items.append({
                'type': 'video',
                'media_obj': media.document,
                'file_id': media.document.id
            })
        
        return media_items

    async def _download_media_batch(self, client: TelegramClient, media_items: List[Dict]) -> List[Dict]:
        self.logger.info(f"Starting download of {len(media_items)} media files...")
        start_time = time.time()
        downloaded = 0
        
        async def _download_with_progress(item):
            nonlocal downloaded
            try:
                path = await self._download_media_file(client, item['media_obj'], item['type'])
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
            {**item, 'path': path} 
            for item, path in zip(media_items, downloaded_paths)
            if not isinstance(path, Exception) and path
        ]

    async def _download_media_file(self, client: TelegramClient, media, media_type: str) -> Optional[str]:
        async with self.download_semaphore:
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

                

class EnhancedUserbotService(UserbotService):
    def __init__(self, api_id: int, api_hash: str, openai_key: str = None, **kwargs):
        super().__init__(api_id, api_hash, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.openai_key = openai_key
        self._openai_client = None
        self._semaphore = asyncio.Semaphore(10)

    @property
    def openai_client(self):
        if not self._openai_client and self.openai_key:
            self._openai_client = openai.AsyncOpenAI(api_key=self.openai_key)
        return self._openai_client

    async def get_last_posts(self, flow: FlowDTO, limit: int = 10) -> List[PostDTO]:
        try:
            start_time = time.time()
            raw_posts = await super().get_last_posts(flow.sources, limit)
            
            processed_posts = await self._process_posts_parallel(raw_posts, flow)
            
            self.logger.info(f"Processed {len(processed_posts)} posts in {time.time() - start_time:.2f}s")
            return processed_posts
        except Exception as e:
            self.logger.error(f"Error getting posts: {str(e)}", exc_info=True)
            return []

    async def _process_posts_parallel(self, raw_posts: List[Dict], flow: FlowDTO) -> List[PostDTO]:
        tasks = []
        for raw_post in raw_posts:
            task = self._safe_process_post(raw_post, flow)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, PostDTO)]

    async def _safe_process_post(self, raw_post: Dict, flow: FlowDTO) -> Optional[PostDTO]:
        try:
            return await self._process_single_post(raw_post, flow)
        except Exception as e:
            self.logger.warning(f"Post processing failed: {str(e)}")
            return None

    async def _process_single_post(self, raw_post: Dict, flow: FlowDTO) -> Optional[PostDTO]:
        post_dto = PostDTO.from_raw_post(raw_post)
        
        if not post_dto.content:
            return None

        if isinstance(post_dto.content, list):
            post_dto.content = " ".join(filter(None, post_dto.content))
        
        if 'original_link' in raw_post:
            post_dto.original_link = raw_post['original_link']
        if 'original_date' in raw_post:
            post_dto.original_date = raw_post['original_date']
        
        try:
            processed_text = await self._process_content(post_dto.content, flow)
            if isinstance(processed_text, list):
                processed_text = " ".join(filter(None, processed_text))
                
            return post_dto.copy(update={
                'content': processed_text,
                'flow_id': flow.id,
                'original_link': post_dto.original_link,
                'original_date': post_dto.original_date
            })
        except Exception as e:
            self.logger.error(f"Error processing post: {str(e)}")
            return None

    async def _process_content(self, text: str, flow: FlowDTO) -> str:
        text = await DefaultContentProcessor().process(text)
        
        if self.openai_key:
            async with self._semaphore:
                text = await self._process_with_chatgpt(text, flow)
        
        if flow.signature:
            text = f"{text}\n\n{flow.signature}"
        
        return text

    async def _process_with_chatgpt(self, text: str, flow: FlowDTO) -> str:
        processor = ChatGPTContentProcessor(
            api_key=self.openai_key,
            flow=flow,
            max_retries=2,
            timeout=15.0
        )
        return await processor.process(text)

    # async def _process_media(self, media_items: List[Dict]) -> List[Dict]:
    #     return media_items