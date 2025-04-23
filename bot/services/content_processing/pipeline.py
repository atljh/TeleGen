from typing import List, Dict
from bot.database.dtos.dtos import PostDTO
from bot.services.content_processing.processors import ContentProcessor

class PostProcessingPipeline:
    def __init__(self, processors: List[ContentProcessor]):
        self.processors = processors

    async def process_post(self, raw_post: Dict) -> PostDTO:
        post_dto = PostDTO.from_raw_post(raw_post)
        
        processed_text = post_dto.content
        for processor in self.processors:
            processed_text = await processor.process_text(processed_text)
        
        return post_dto.copy(update={'content': processed_text})