from pydantic import BaseModel
from datetime import datetime

class UserDTO(BaseModel):
    telegram_id: int
    username: str | None
    subscription_status: bool
    subscription_end_date: datetime | None

    class Config:
        from_attributes = True