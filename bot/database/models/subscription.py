from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SubscriptionDTO(BaseModel):
    id: int
    user_id: int
    channel_id: int
    subscription_type: str
    start_date: datetime
    end_date: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)