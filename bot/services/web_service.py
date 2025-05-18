import os
import time
import asyncio
import logging
import tempfile
from datetime import datetime
from typing import Optional, List, Dict, AsyncGenerator
from contextlib import asynccontextmanager

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from bot.database.dtos.dtos import FlowDTO, PostDTO
from admin_panel.admin_panel.models import PostImage, Post
from bot.services.content_processing.processors import ChatGPTContentProcessor, DefaultContentProcessor
from bot.services.aisettings_service import AISettingsService
from bot.services.user_service import UserService
from bot.utils.notifications import notify_admins

class WebService:
    def __init__(
        self,
        aisettings_service: AISettingsService,
        user_service: UserService,
        openai_key: str = None,
    ):
        self.logger = logging.getLogger(__name__)
        self.openai_key = openai_key
        self._semaphore = asyncio.Semaphore(10)
        self.user_service = user_service
        self.aisettings_service = aisettings_service
        self.download_semaphore = asyncio.Semaphore(5)

    async def get_last_posts(self, flow: FlowDTO, limit: int = 10) -> List[PostDTO]:
        try:
            start_time = time.time()
            raw_posts = await self._fetch_web_posts(flow.sources, limit)
            processed_posts = await self._process_posts_parallel(raw_posts, flow)
            self.logger.info(f"Processed {len(processed_posts)} posts in {time.time() - start_time:.2f}s")
            return processed_posts
        except Exception as e:
            self.logger.error(f"Error getting posts: {str(e)}", exc_info=True)
            return []

    async def _fetch_web_posts(self, sources: List[Dict], limit: int) -> List[Dict]:
        result = []
        source_limits = {}
        
        base_limit = max(1, limit // len(sources))
        for source in sources:
            source_limits[source['link']] = base_limit
        
        remaining = limit - base_limit * len(sources)
        for source in sources[:remaining]:
            source_limits[source['link']] += 1

        for source in sources:
            if len(result) >= limit:
                break

            if source['type'] != 'web':
                continue

            try:
                remaining_for_source = source_limits[source['link']]
                if remaining_for_source <= 0:
                    continue

                post_data = await self._process_web_source(source, remaining_for_source)
                if post_data:
                    result.append(post_data)
                    source_limits[source['link']] -= 1

            except Exception as e:
                self.logger.error(f"Error processing source {source['link']}: {str(e)}")
                continue

        return result

    async def _process_web_source(self, source: Dict, limit: int) -> Optional[Dict]:
        try:
            async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
                result = await crawler.arun(
                    url=source['link'],
                    config=BrowserConfig(
                        enable_js=True,
                        wait_for_page_load=2,
                        scroll_to_bottom=True,
                        extract_metadata=True
                    )
                )

            # Обрабатываем контент страницы
            content = result.markdown or result.cleaned_text or result.raw_html
            if not content:
                return None

            # Извлекаем медиа (изображения/видео)
            media_items = []
            if result.metadata and result.metadata.get('images'):
                media_items = [
                    {'type': 'image', 'url': img, 'file_id': hash(img)}
                    for img in result.metadata['images'][:5]  # Берем первые 5 изображений
                ]

            # Загружаем медиа файлы
            downloaded_media = await self._download_media_batch(media_items)

            return {
                'text': content[:5000],  # Ограничиваем размер текста
                'media': downloaded_media,
                'is_album': False,
                'album_size': 0,
                'original_link': source['link'],
                'original_date': datetime.now(),
                'source_url': source['link'],
                'source_id': f"web_{hash(source['link'])}"
            }

        except Exception as e:
            self.logger.error(f"Error processing web source {source['link']}: {str(e)}")
            return None

    async def _download_media_batch(self, media_items: List[Dict]) -> List[Dict]:
        if not media_items:
            return []

        self.logger.info(f"Starting download of {len(media_items)} media files...")
        start_time = time.time()
        downloaded = 0
        
        async def _download_with_progress(item):
            nonlocal downloaded
            try:
                path = await self._download_media_file(item['url'], item['type'])
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

    async def _download_media_file(self, url: str, media_type: str) -> Optional[str]:
        async with self.download_semaphore:
            try:
                # Здесь должна быть реализация загрузки файла по URL
                # Например, используя aiohttp или requests
                # Для примера просто создаем временный файл
                with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{media_type}') as tmp_file:
                    tmp_path = tmp_file.name
                
                # В реальной реализации здесь должен быть код загрузки файла
                # Например:
                # async with aiohttp.ClientSession() as session:
                #     async with session.get(url) as response:
                #         with open(tmp_path, 'wb') as f:
                #             f.write(await response.read())
                
                if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                    return tmp_path
                
                os.unlink(tmp_path)
                return None
                
            except Exception as e:
                self.logger.error(f"Media download failed: {str(e)}")
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                return None

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
        if 'source_url' in raw_post:
            post_dto.source_url = raw_post['source_url']   
        if 'source_id' in raw_post:
            post_dto.source_id = raw_post['source_id']

        try:
            processed_text = await self._process_content(post_dto.content, flow)
            if isinstance(processed_text, list):
                processed_text = " ".join(filter(None, processed_text))
                
            return post_dto.copy(update={
                'content': processed_text,
                'flow_id': flow.id,
                'source_url': post_dto.source_url,
                'source_id': post_dto.source_id,
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
        user = await self.user_service.get_user_by_flow(flow)
        processor = ChatGPTContentProcessor(
            api_key=self.openai_key,
            flow=flow,
            max_retries=2,
            timeout=15.0,
            aisettings_service=self.aisettings_service
        )
        return await processor.process(text, user.id)