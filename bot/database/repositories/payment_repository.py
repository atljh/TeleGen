from admin_panel.admin_panel.models import Payment, User
from bot.database.exceptions import PaymentNotFoundError


class PaymentRepository:
    async def create_payment(
        self,
        user: User,
        amount: float,
        payment_method: str,
        is_successful: bool = False,
    ) -> Payment:
        return await Payment.objects.acreate(
            user=user,
            amount=amount,
            payment_method=payment_method,
            is_successful=is_successful,
        )

    async def get_payment_by_id(self, payment_id: int) -> Payment:
        try:
            return await Payment.objects.aget(id=payment_id)
        except Payment.DoesNotExist:
            raise PaymentNotFoundError(f"Payment with id={payment_id} not found.")

    async def update_payment(self, payment: Payment) -> Payment:
        await payment.asave()
        return payment

    async def delete_payment(self, payment: Payment):
        await payment.adelete()
