import logging
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, validator
from datetime import datetime
from admin_panel.admin_panel.models import Channel, User
# from bot.services.content_processing.processors import ContentProcessor


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
    notifications: bool
    timezone: str

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class ContentLength(str, Enum):
    to_100 = 'to_100'
    to_300 = 'to_300'
    to_1000 = 'to_1000'

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

class PostStatus(str, Enum):
    DRAFT = 'draft'
    SCHEDULED = 'scheduled'
    PUBLISHED = 'published'

class PostImageDTO(BaseModel):
    url: str
    order: int

class PostDTO(BaseModel):
    id: Optional[int] = None
    flow_id: int
    content: str
    original_content: str = None
    source_id: str
    source_url: Optional[str] = None
    publication_date: Optional[datetime] = None
    status: PostStatus = PostStatus.DRAFT
    original_link: Optional[str] = None
    created_at: datetime
    original_date: Optional[datetime] = None
    scheduled_time: Optional[datetime] = None
    media_type: Optional[MediaType] = None
    media_url: Optional[str] = None
    images: List[PostImageDTO] = []
    video_url: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None,
            PostStatus: lambda v: v.value,
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
            if media['type'] == 'video'),
            None
        )

        status = PostStatus.DRAFT
        if raw_post.get('is_published', False):
            status = PostStatus.PUBLISHED
        elif raw_post.get('scheduled_time'):
            status = PostStatus.SCHEDULED

        return cls(
            content=raw_post.get('text', ''),
            source_url=raw_post.get('source', {}).get('link'),
            images=images,
            video_url=video_url,
            status=status,
            original_link=raw_post.get('original_link'),
            original_date=raw_post.get('original_date'),
            source_id=raw_post.get('source_id'),
            flow_id=0,
            created_at=datetime.now()
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

        status = PostStatus(post.status)

        return cls(
            id=post.id,
            flow_id=post.flow.id,
            content=post.content,
            source_url=post.source_url,
            original_link=post.original_link,
            original_date=post.original_date,
            source_id=post.source_id,
            publication_date=post.publication_date,
            status=status,
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
    flow_id: int
    prompt: str
    style: str = None
    role: str = None
    role_content: str = None
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
