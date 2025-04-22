from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, validator
from datetime import datetime
from admin_panel.admin_panel.models import Channel, User
from bot.services.content_processing.processors import ContentProcessor


class UserDTO(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    subscription_type: str | None
    subscription_status: bool
    subscription_end_date: datetime | None
    payment_method: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class ChannelDTO(BaseModel):
    id: int
    user_id: int
    channel_id: str
    name: str
    description: str | None
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class ContentLength(str, Enum):
    SHORT = "to_100"      # До 100 знаків
    MEDIUM = "to_300"     # До 300 знаків
    LONG = "to_1000"      # До 1000 знаків

class GenerationFrequency(str, Enum):
    HOURLY = "hourly"        # Кожну годину
    EVERY_12_HOURS = "12h"   # Раз на 12 годин
    DAILY = "daily"          # Раз на день

class FlowDTO(BaseModel):
    id: int
    channel_id: int
    name: str
    theme: str
    sources: list[dict]       # Список посилань на джерела
    content_length: ContentLength
    use_emojis: bool
    use_premium_emojis: bool
    title_highlight: bool    # Виділення заголовків
    cta: bool
    frequency: str
    signature: str | None    # Підпис до постів
    flow_volume: int         # Кількість постів у флоу
    ad_time: str | None      # Час для рекламних топів (HH:MM)
    created_at: datetime
    updated_at: datetime | None
    next_generation_time: Optional[datetime] = None
    last_generated_at: Optional[datetime] = None


    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"

class PostImageDTO(BaseModel):
    url: str
    order: int

class PostDTO(BaseModel):
    id: int
    flow_id: int
    content: str
    source_url: Optional[str] = None
    publication_date: Optional[datetime] = None
    is_published: bool
    is_draft: bool
    created_at: datetime
    scheduled_time: Optional[datetime] = None

    media_url: Optional[str] = None
    media_type: Optional[MediaType] = None
    
    images: List[PostImageDTO] = []
    video_url: Optional[str] = None
    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None
        }

    @property
    def is_album(self) -> bool:
        return len(self.images) > 1
    
    @property
    def main_media(self) -> Optional[Dict]:
        if self.images:
            return {"type": MediaType.IMAGE, "url": self.images[0].url}
        elif self.video_url:
            return {"type": MediaType.VIDEO, "url": self.video_url}
        return None
    
    async def process_content(self, processors: List[ContentProcessor]) -> "PostDTO":
        processed_text = self.content
        for processor in processors:
            processed_text = await processor.process_text(processed_text)
        
        return self.copy(update={"content": processed_text})
    
    def to_telegram_dict(self) -> Dict[str, Any]:
        return {
            "text": self.content,
            "images": [{"url": img.url, "order": img.order} for img in self.images],
            "video_url": self.video_url,
            "is_album": len(self.images) > 1
        }

    @property
    def has_media(self) -> bool:
        return len(self.images) > 0 or self.video_url is not None

    @classmethod
    def from_raw_post(cls, raw_post: Dict) -> 'PostDTO':
        images = [
            PostImageDTO(url=media['path'], order=i)
            for i, media in enumerate(raw_post.get('media', []))
            if media['type'] == 'image'
        ]
        
        video_url = next(
            (media['path'] for media in raw_post.get('media', [])
            if media['type'] == 'video'
        ), None)

        return cls(
            content=raw_post.get('text', ''),
            is_album=raw_post.get('is_album', False),
            images=images,
            video_url=video_url
        )


    @classmethod
    def from_orm(cls, post, images=None):
        if images is None:
            images = list(post.images.all().order_by('order'))
        
        image_dtos = [PostImageDTO(url=img.image.url, order=img.order) for img in images]

        media_type = None
        if image_dtos:
            media_type = MediaType.IMAGE
        elif post.video:
            media_type = MediaType.VIDEO

        return cls(
            id=post.id,
            flow_id=post.flow_id,
            content=post.content,
            source_url=post.source_url,
            publication_date=post.publication_date,
            is_published=post.is_published,
            is_draft=post.is_draft,
            created_at=post.created_at,
            scheduled_time=post.scheduled_time,
            media_url=image_dtos[0].url if image_dtos else None,
            media_type=media_type,
            images=image_dtos,
            video_url=post.video.url if post.video else None
        )

class DraftDTO(BaseModel):
    id: int
    user_id: int
    post_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SubscriptionDTO(BaseModel):
    id: int
    user_id: int
    channel_id: int
    subscription_type: str
    start_date: datetime
    end_date: datetime
    is_active: bool

    class Config:
        from_attributes = True

class PaymentDTO(BaseModel):
    id: int
    user_id: int
    amount: float
    payment_method: str
    payment_date: datetime
    is_successful: bool

    class Config:
        from_attributes = True

class AISettingsDTO(BaseModel):
    id: int
    user_id: int
    prompt: str
    style: str
    created_at: datetime

    class Config:
        from_attributes = True

class StatisticsDTO(BaseModel):
    id: int
    user_id: int
    channel_id: int
    total_posts: int
    total_views: int
    total_likes: int
    last_updated: datetime

    class Config:
        from_attributes = True
