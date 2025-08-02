import logging
from bot.database.dtos import PaymentDTO
from bot.database.repositories import PaymentRepository, UserRepository

class PaymentService:
    def __init__(
        self,
        payment_repository: PaymentRepository,
        user_repository: UserRepository,
        logger: logging.Logger | None = None
    ):
        self.payment_repository = payment_repository
        self.user_repository = user_repository
        self.logger = logger or logging.getLogger(__name__)

    async def create_payment(
            self,
            user_id: int,
            amount: float,
            payment_method: str,
            is_successful: bool = False
        ) -> PaymentDTO:
       user = await self.user_repository.get_user_by_id(user_id)
       payment = await self.payment_repository.create_payment(
           user=user,
           amount=amount,
           payment_method=payment_method,
           is_successful=is_successful
       )
       return PaymentDTO.from_orm(payment)
    
    async def get_payment(self, payment_id: int) -> PaymentDTO:
        payment = await self.payment_repository.get_payment_by_id(payment_id)
        return PaymentDTO.from_orm(payment)
    
    async def update_payment(self, payment_id: int) -> PaymentDTO:
        payment = await self.payment_repository.get_payment_by_id(payment_id)
        updated_payment = await self.payment_repository.update_payment(payment)
        return PaymentDTO.from_orm(updated_payment)
    
    async def delete_payment(self, payment_id: int):
        payment = await self.payment_repository.get_payment_by_id(payment_id)
        await self.payment_repository.delete_payment(payment)