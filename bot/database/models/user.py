from datetime import datetime
from pydantic import BaseModel
from typing import Any, Self

class UserDTO(BaseModel):
    id: int
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    subscription_type: str | None = None
    subscription_status: bool = False
    subscription_end_date: datetime | None = None
    payment_method: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}

    @classmethod
    def from_orm(cls, obj: Any) -> Self:
        return super().model_validate(obj)