import logging
import uuid

import aiohttp

from bot.database.models import PaymentDTO
from bot.database.repositories import PaymentRepository, UserRepository


class PaymentService:
    MONOBANK_API = "https://api.monobank.ua/api/merchant/invoice/create"
    CRYPTOBOT_API = "https://testnet-pay.crypt.bot/api/createInvoice"

    def __init__(
        self,
        payment_repository: PaymentRepository,
        user_repository: UserRepository,
        monobank_token: str,
        cryptobot_token: str,
        logger: logging.Logger | None = None,
    ):
        self.payment_repository = payment_repository
        self.user_repository = user_repository
        self.monobank_token = monobank_token
        self.cryptobot_token = cryptobot_token
        self.logger = logger or logging.getLogger(__name__)

    async def create_payment(
        self,
        user_id: int,
        amount: float,
        payment_method: str,
        description: str = "Оплата підписки",
        currency: str = "UAH",
        is_successful: bool = False,
    ) -> PaymentDTO:
        user = await self.user_repository.get_user_by_telegram_id(user_id)
        order_id = f"ORDER_{user_id}_{uuid.uuid4().hex[:8]}"

        pay_url = None
        if payment_method == "monobank":
            pay_url = await self._create_monobank_invoice(order_id, amount, description)
        elif payment_method == "cryptobot":
            pay_url = await self._create_cryptobot_invoice(
                order_id, amount, description, currency
            )
        else:
            raise ValueError(f"Unsupported payment method: {payment_method}")

        payment = await self.payment_repository.create_payment(
            user=user,
            amount=amount,
            payment_method=payment_method,
            pay_url=pay_url,
            order_id=order_id,
            is_successful=is_successful,
        )

        return PaymentDTO.from_orm(payment)

    async def _create_monobank_invoice(
        self, order_id: str, amount: float, description: str
    ) -> str:
        headers = {"X-Token": self.monobank_token}
        payload = {
            "amount": int(float(amount) * 100),
            "ccy": 980,  # UAH
            "merchantPaymInfo": {
                "reference": order_id,
                "destination": description,
            },
            "redirectUrl": "https://t.me/neurogram_soft_bot",
            "webHookUrl": "https://postomat.xyz/webhook/monobank/",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.MONOBANK_API, json=payload, headers=headers
            ) as resp:
                data = await resp.json()
                if "pageUrl" not in data:
                    raise RuntimeError(f"Monobank error: {data}")
                return data["pageUrl"]

    async def _create_cryptobot_invoice(
        self, order_id: str, amount: float, description: str, currency: str
    ) -> str:
        headers = {"Crypto-Pay-API-Token": self.cryptobot_token}
        payload = {
            "asset": "JET",
            "amount": str(amount),
            "description": description,
            "hidden_message": f"Order {order_id}",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.CRYPTOBOT_API, json=payload, headers=headers
            ) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    raise RuntimeError(f"CryptoBot error: {data}")
                return data["result"]["pay_url"]

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
