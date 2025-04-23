from datetime import datetime
import os
import tempfile
import asyncio
import logging
from typing import Optional, List, Dict, AsyncGenerator
from contextlib import asynccontextmanager
from telethon import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest

from bot.database.dtos.dtos import FlowDTO, PostDTO
from bot.services.content_processing.processors import ChatGPTContentProcessor, ContentProcessor, DefaultContentProcessor
from  bot.services.content_processing.pipeline import PostProcessingPipeline

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

            texts = []
            media_items = []
            
            for msg in album_messages:
                if msg.text:
                    texts.append(msg.text)
                if msg.media:
                    media_items.extend(await self._extract_media(client, msg.media))
            
            post_data = {
                'text': "\n\n".join(texts) if texts else "",
                'media': media_items,
                'is_album': True,
                'album_size': len(album_messages)
            }
            
            return post_data
            
        except Exception as e:
            logging.error(f"Error processing album: {str(e)}")
            return None

    async def _process_message(self, client: TelegramClient, msg) -> Optional[Dict]:
        if not msg.text and not msg.media:
            return None

        post_data = {
            'text': msg.text or '',
            'media': [],
            'is_album': False,
            'album_size': 0
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
        

class EnhancedUserbotService(UserbotService):
    def __init__(self, api_id: int, api_hash: str, openai_key: str = None, **kwargs):
        super().__init__(api_id, api_hash, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.openai_key = openai_key

    async def get_last_posts(self, flow: FlowDTO, limit: int = 10) -> List[PostDTO]:
        try:
            raw_posts = await super().get_last_posts(flow.sources, limit)
            return await self._process_posts(raw_posts, flow)
        except Exception as e:
            self.logger.error(f"Error getting posts for flow {flow.id}: {str(e)}", exc_info=True)
            return []

    async def _process_posts(self, raw_posts: List[Dict], flow: FlowDTO) -> List[PostDTO]:
        processed_posts = []
        
        for raw_post in raw_posts:
            try:
                post_dto = await self._process_single_post(raw_post, flow)
                if post_dto:
                    processed_posts.append(post_dto)
            except Exception as e:
                self.logger.warning(f"Skipping post in flow {flow.id}: {str(e)}")
                continue
                
        return processed_posts

    async def _process_single_post(self, raw_post: Dict, flow: FlowDTO) -> Optional[PostDTO]:
        post_dto = PostDTO.from_raw_post(raw_post)
        
        if not post_dto.content:
            return None

        processed_text = await DefaultContentProcessor().process(post_dto.content)
        
        if self.openai_key and getattr(flow, 'use_ai', False):
            try:
                processor = ChatGPTContentProcessor(
                    api_key=self.openai_key,
                    flow=flow
                )
                processed_text = await processor.process(processed_text)
            except Exception as e:
                self.logger.error(f"ChatGPT processing failed for flow {flow.id}: {str(e)}")

        else:
            if flow.signature:
                processed_text = f"{processed_text}\n\n{flow.signature}"
                
            if flow.use_emojis:
                processed_text = await self._apply_emoji(processed_text, flow)
                
            if flow.cta:
                processed_text = await self._apply_cta(processed_text, flow.theme)

        return post_dto.copy(update={'content': processed_text})

    async def _apply_emoji(self, text: str, flow: FlowDTO) -> str:
        emoji_map = {
            'tech': ['⚙️', '🔧', '💻'],
            'news': ['📰', '🗞️', '🌐'],
            'fun': ['😂', '🤣', '🎉']
        }
        
        emojis = emoji_map.get(flow.theme, ['✨', '🌟'])
        return f"{emojis[0]} {text} {emojis[-1]}"

    async def _apply_cta(self, text: str, theme: str) -> str:
        cta_phrases = {
            'tech': "💬 Обсудим в комментариях!",
            'news': "📌 Подпишитесь для свежих новостей!",
            'fun': "😂 Нравится? Ставь лайк!"
        }
        return f"{text}\n\n{cta_phrases.get(theme, 'Подпишитесь для новых обновлений!')}"