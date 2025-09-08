from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel


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
