from typing import List, Dict, Optional
from bot.database.models import PostDTO
from bot.services.content_processing.processors import ContentProcessor
import logging

class PostProcessingPipeline:
    def __init__(self, processors: List[ContentProcessor]):
        self.processors = processors
        self.logger = logging.getLogger(__name__)

    async def process_post(self, raw_post: Dict) -> Optional[PostDTO]:
        try:
            post_dto = PostDTO.from_raw_post(raw_post)
            if not post_dto.content:
                self.logger.warning("Empty content in post")
                return None
            
            processed_text = post_dto.content
            for processor in self.processors:
                processed_text = await processor.process(processed_text)
                if not processed_text:
                    self.logger.warning(f"Processor {type(processor).__name__} returned empty text")
                    break
            
            return post_dto.copy(update={'content': processed_text})
            
        except Exception as e:
            self.logger.error(f"Error processing post: {str(e)}", exc_info=True)
            return None