from enum import Enum
from typing import Optional
from pydantic import BaseModel, validator
from datetime import datetime
from admin_panel.admin_panel.models import Channel, User


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
    WEEKLY = "weekly"        # Раз на тиждень

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

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

class MediaType(str, Enum):
    IMAGE = 'image'
    VIDEO = 'video'


class PostDTO(BaseModel):
    id: int
    flow_id: int
    content: str
    source_url: Optional[str] = None
    publication_date: Optional[datetime] = None
    is_published: bool
    is_draft: bool
    created_at: datetime
    
    media_url: Optional[str] = None
    media_type: Optional[MediaType] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None
        }

    @classmethod
    def from_orm(cls, post):
        media_url = None
        media_type = None
        thumbnail_url = None
        
        if post.image:
            media_url = post.image.url
            media_type = MediaType.IMAGE
        elif post.video:
            media_url = post.video.url
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
            media_url=media_url,
            media_type=media_type,
            thumbnail_url=thumbnail_url
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
