from enum import Enum
from pydantic import BaseModel
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
    SHORT = "short"      # До 300 знаків
    MEDIUM = "medium"    # 300-1000 знаків
    LONG = "long"        # Понад 1000 знаків

class GenerationFrequency(str, Enum):
    HOURLY = "hourly"        # Кожну годину
    DAILY = "daily"          # Раз на день
    WEEKLY = "weekly"        # Раз на тиждень
    CUSTOM = "custom"        # Користувацький графік

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
    frequency: GenerationFrequency
    signature: str | None    # Підпис до постів
    flow_volume: int         # Кількість постів у флоу
    ad_time: str | None      # Час для рекламних топів (HH:MM)
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

class PostDTO(BaseModel):
    id: int
    flow_id: int
    content: str
    source_url: str
    publication_date: datetime
    is_published: bool
    is_draft: bool
    created_at: datetime

    class Config:
        from_attributes = True

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
