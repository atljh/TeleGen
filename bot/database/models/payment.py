from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PaymentDTO(BaseModel):
    id: int
    user_id: int
    amount: float
    payment_method: str
    payment_date: datetime
    is_successful: bool

    model_config = ConfigDict(
        from_attributes=True,
    )
