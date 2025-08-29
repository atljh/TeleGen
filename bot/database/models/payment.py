from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Any, Self

class PaymentDTO(BaseModel):
    id: int
    user_id: int
    amount: float
    payment_method: str
    payment_date: datetime
    is_successful: bool

    class Config:
        from_attributes = True