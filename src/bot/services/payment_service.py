import logging
import uuid

import aiohttp

from bot.database.models import PaymentDTO
from bot.database.repositories import PaymentRepository, UserRepository


class PaymentService:
    def __init__(
        self,
        payment_repository: PaymentRepository,
        user_repository: UserRepository,
        monobank_token: str,
        cryptobot_token: str,
        monobank_api_url: str,
        monobank_redirect_url: str,
        monobank_webhook_url: str,
        cryptobot_api_url: str,
        logger: logging.Logger | None = None,
    ):
        self.payment_repository = payment_repository
        self.user_repository = user_repository
        self.monobank_token = monobank_token
        self.cryptobot_token = cryptobot_token
        self.logger = logger or logging.getLogger(__name__)
        self.monobank_api_url = monobank_api_url
        self.monobank_redirect_url = monobank_redirect_url
        self.monobank_webhook_url = monobank_webhook_url
        self.cryptobot_api_url = cryptobot_api_url

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

        reference = uuid.uuid4().hex
        order_id = f"ORDER_{user_id}_{uuid.uuid4().hex[:8]}"

        pay_url = None
        if payment_method == "monobank":
            pay_url = await self._create_monobank_invoice(
                reference, amount, description
            )
        elif payment_method == "cryptobot":
            pay_url = await self._create_cryptobot_invoice(
                order_id, amount, description, currency
            )
        else:
            raise ValueError(f"Unsupported payment method: {payment_method}")

        external_id = reference if payment_method == "monobank" else None

        payment = await self.payment_repository.create_payment(
            user=user,
            amount=amount,
            payment_method=payment_method,
            pay_url=pay_url,
            order_id=order_id,
            external_id=external_id,
            is_successful=is_successful,
        )

        return PaymentDTO.from_orm(payment)

    async def _create_monobank_invoice(
        self, reference: str, amount: float, description: str
    ) -> str:
        headers = {"X-Token": self.monobank_token}
        payload = {
            "amount": int(float(amount) * 100),
            "ccy": 980,
            "merchantPaymInfo": {
                "reference": reference,
                "destination": description,
            },
            "redirectUrl": self.monobank_redirect_url,
            "webHookUrl": self.monobank_webhook_url,
        }

        self.logger.info(f"Creating Monobank invoice with reference: {reference}")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.monobank_api_url, json=payload, headers=headers
            ) as resp:
                data = await resp.json()
                if "pageUrl" not in data:
                    self.logger.error(f"Monobank API error: {data}")
                    raise RuntimeError(f"Monobank error: {data}")

                self.logger.info(f"Monobank invoice created: {data.get('invoiceId')}")
                return data["pageUrl"]

    async def _create_cryptobot_invoice(
        self, order_id: str, amount: float, description: str, currency: str
    ) -> str:
        headers = {"Crypto-Pay-API-Token": self.cryptobot_token}
        payload = {
            "asset": "USDT",
            "amount": str(amount),
            "description": description,
            "hidden_message": f"Order {order_id}",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.cryptobot_api_url, json=payload, headers=headers
            ) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    self.logger.error(f"CryptoBot API error: {data}")
                    raise RuntimeError(f"CryptoBot error: {data}")

                result = data["result"]
                self.logger.info(
                    f"CryptoBot invoice created: {result.get('invoice_id')}"
                )
                return result["pay_url"]

    async def get_payment_by_external_id(self, external_id: str) -> PaymentDTO:
        payment = await self.payment_repository.get_payment_by_external_id(external_id)
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
