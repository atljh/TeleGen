import os
import asyncio
import logging
from typing import Optional, List, Dict, Any

from telethon import TelegramClient

from ..types import MediaInfo, DownloadError

class DownloadService:
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)

    async def download_media_with_retry(
        self,
        client: TelegramClient,
        media: Any,
        file_path: str,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None
    ) -> bool:
        max_retries = max_retries or self.max_retries
        retry_delay = retry_delay or self.retry_delay

        for attempt in range(max_retries):
            try:
                success = await self._download_single_attempt(client, media, file_path)
                if success:
                    return True
                    
            except Exception as e:
                self.logger.warning(f"Download attempt {attempt + 1} failed: {str(e)}")
                
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))
        
        return False

    async def _download_single_attempt(self, client: TelegramClient, media: Any, file_path: str) -> bool:
        await client.download_media(media, file=file_path)
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return True
        
        if os.path.exists(file_path):
            os.unlink(file_path)
            
        return False

    async def download_media_batch(
        self,
        client: TelegramClient,
        media_items: List[MediaInfo],
        output_dir: str,
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def download_with_semaphore(media_item: MediaInfo):
            async with semaphore:
                return await self._download_single_media(client, media_item, output_dir)

        tasks = [download_with_semaphore(media_item) for media_item in media_items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            result for result in results 
            if not isinstance(result, Exception) and result is not None
        ]

    async def _download_single_media(
        self,
        client: TelegramClient,
        media_item: MediaInfo,
        output_dir: str
    ) -> Optional[Dict[str, Any]]:
        try:
            file_name = f"{media_item['file_id']}_{media_item['type']}"
            file_path = os.path.join(output_dir, file_name)
            
            success = await self.download_media_with_retry(
                client, media_item['media_obj'], file_path
            )
            
            if success:
                return {
                    **media_item,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'success': True
                }
            
        except Exception as e:
            self.logger.error(f"Media download failed: {str(e)}")
            
        return None

    async def validate_media_file(self, file_path: str, min_size: int = 1024) -> bool:
        return (
            os.path.exists(file_path) and
            os.path.isfile(file_path) and
            os.path.getsize(file_path) >= min_size
        )

    async def cleanup_downloads(self, file_paths: List[str]):
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                self.logger.warning(f"Failed to cleanup file {file_path}: {str(e)}")