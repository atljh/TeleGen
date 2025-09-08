from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, field_serializer


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

    model_config = ConfigDict(
        from_attributes=True
    )

    @field_serializer("created_at")
    def serialize_created_at(self, v: datetime):
        return v.isoformat()

    @classmethod
    def from_orm(cls, obj: Any) -> Self:
        return super().model_validate(obj)
