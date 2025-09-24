from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SubscriptionDTO(BaseModel):
    id: int
    user_id: int
    tariff_period_id: int
    start_date: datetime
    end_date: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
