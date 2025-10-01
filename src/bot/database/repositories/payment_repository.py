from admin_panel.models import Payment, User
from bot.database.exceptions import PaymentNotFoundError


class PaymentRepository:
    async def create_payment(
        self,
        user: User,
        amount: float,
        payment_method: str,
        is_successful: bool = False,
        order_id: str | None = None,
        pay_url: str | None = None,
    ) -> Payment:
        return await Payment.objects.acreate(
            user=user,
            amount=amount,
            payment_method=payment_method,
            is_successful=is_successful,
            order_id=order_id,
            pay_url=pay_url,
        )

    async def get_payment_by_id(self, payment_id: int) -> Payment:
        try:
            return await Payment.objects.aget(id=payment_id)
        except Payment.DoesNotExist as e:
            raise PaymentNotFoundError(
                f"Payment with id={payment_id} not found."
            ) from e

    async def get_payment_by_external_id(self, external_id: str) -> Payment:
        return await Payment.objects.aget(external_id=external_id)

    async def update_payment(self, payment: Payment) -> Payment:
        await payment.asave()
        return payment

    async def delete_payment(self, payment: Payment):
        await payment.adelete()
