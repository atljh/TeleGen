import logging
from datetime import timedelta

from asgiref.sync import async_to_sync
from django.utils import timezone

from .models import Payment, PromoCode, Subscription, TariffPeriod

logger = logging.getLogger(__name__)


class PaymentHandler:
    def handle_monobank_webhook(self, data: dict):
        reference = data.get("reference")
        status = data.get("status")
        invoice_id = data.get("invoiceId")

        logger.info(
            f"Processing Monobank webhook: reference={reference}, status={status}, invoiceId={invoice_id}"
        )

        if not reference:
            logger.warning("No reference in Monobank webhook")
            return

        try:
            payment = Payment.objects.get(external_id=reference)
        except Payment.DoesNotExist:
            logger.error(f"Payment with external_id={reference} not found")
            try:
                payment = Payment.objects.get(order_id=reference)
                logger.info(f"Found payment by order_id: {reference}")
            except Payment.DoesNotExist:
                logger.error(f"Payment not found for reference: {reference}")
                return

        if status == "success":
            payment.is_successful = True
            payment.save(update_fields=["is_successful"])
            logger.info(
                f"Payment {payment.id} marked as successful (Monobank invoice: {invoice_id})"
            )

            self.activate_subscription(payment)

        elif status in ["failure", "expired"]:
            payment.is_successful = False
            payment.save(update_fields=["is_successful"])
            logger.warning(
                f"Payment {payment.id} failed/expired (Monobank invoice: {invoice_id}, status: {status})"
            )

        else:
            logger.info(
                f"Payment {payment.id} status: {status} (Monobank invoice: {invoice_id})"
            )

    def handle_cryptobot_webhook(self, data: dict):
        payload = data.get("payload", {})
        invoice_id = payload.get("invoice_id")
        status = payload.get("status")
        hidden_message = payload.get("hidden_message", "")

        logger.info(
            f"Processing CryptoBot webhook: invoice_id={invoice_id}, status={status}"
        )

        payment = None

        if hidden_message:
            try:
                import re

                order_match = re.search(r"Order\s+(\S+)", hidden_message)
                if order_match:
                    order_id = order_match.group(1)
                    payment = Payment.objects.get(order_id=order_id)
                    logger.info(
                        f"Found payment by order_id from hidden_message: {order_id}"
                    )
            except Payment.DoesNotExist:
                logger.warning(
                    f"Payment with order_id from hidden_message not found: {hidden_message}"
                )

        if not payment and invoice_id:
            try:
                payment = Payment.objects.get(external_id=str(invoice_id))
                logger.info(f"Found payment by external_id: {invoice_id}")
            except Payment.DoesNotExist:
                logger.warning(f"Payment with external_id={invoice_id} not found")

        if not payment:
            logger.error(
                f"Payment not found for CryptoBot webhook: invoice_id={invoice_id}, hidden_message={hidden_message}"
            )
            return

        if status == "paid":
            payment.is_successful = True
            payment.save(update_fields=["is_successful"])
            logger.info(f"Payment {payment.id} marked as successful (CryptoBot)")

            self.activate_subscription(payment)

        elif status == "expired":
            payment.is_successful = False
            payment.save(update_fields=["is_successful"])
            logger.info(f"Payment {payment.id} expired (CryptoBot)")

    def activate_subscription(self, payment: Payment):
        try:
            user = payment.user

            tariff_period = payment.tariff_period

            if not tariff_period:
                logger.error(f"No tariff period found for payment {payment.id}")
                return

            # Check if user is trying to downgrade to a lower-tier subscription
            active_subscription = Subscription.objects.filter(
                user=user, is_active=True
            ).select_related('tariff_period__tariff').first()

            if active_subscription:
                current_tariff = active_subscription.tariff_period.tariff
                new_tariff = tariff_period.tariff

                if not new_tariff.is_higher_than(current_tariff) and new_tariff.level != current_tariff.level:
                    logger.warning(
                        f"User {user.telegram_id} attempted to downgrade from "
                        f"{current_tariff.name} (level {current_tariff.level}) to "
                        f"{new_tariff.name} (level {new_tariff.level}). Payment {payment.id} rejected."
                    )
                    return

            active_subscriptions = Subscription.objects.filter(
                user=user, is_active=True
            )

            for subscription in active_subscriptions:
                subscription.is_active = False
                subscription.save(update_fields=["is_active"])
                logger.info(
                    f"Deactivated previous subscription {subscription.id} for user {user.telegram_id}"
                )

            start_date = timezone.now()
            end_date = start_date + timedelta(days=tariff_period.months * 30)

            subscription = Subscription.objects.create(
                user=user,
                tariff_period=tariff_period,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
            )

            payment.subscription = subscription
            payment.save(update_fields=["subscription"])

            logger.info(
                f"Activated subscription {subscription.id} for user {user.telegram_id} "
                f"({tariff_period.tariff.name} for {tariff_period.months} months)"
            )

            self.send_success_notification(user, tariff_period)

        except Exception as e:
            logger.error(
                f"Error activating subscription for payment {payment.id}: {e}",
                exc_info=True,
            )

    def send_success_notification(self, user, tariff_period):
        try:
            from bot.containers import Container

            bot = Container.bot()
            message_text = (
                "🎉 Ваша підписка успішно активована!\n\n"
                f"📋 Тариф: {tariff_period.tariff.name}\n"
                f"⏱️ Термін: {tariff_period.get_months_display()}\n"
                f"💰 Вартість: {tariff_period.price}₴\n\n"
                "Тепер вам доступні всі функції обраного тарифу!"
            )

            async_to_sync(bot.send_message)(chat_id=user.telegram_id, text=message_text)

        except Exception as e:
            logger.error(
                f"Error sending success notification to user {user.telegram_id}: {e}"
            )

    def send_promo_success_notification(self, user, tariff_period, promo_code):
        """Send notification when subscription is activated via promo code"""
        try:
            from bot.containers import Container

            bot = Container.bot()
            message_text = (
                "🎉 Вітаємо! Ваша підписка успішно активована за промокодом!\n\n"
                f"🎫 Промокод: {promo_code.code}\n"
                f"📋 Тариф: {tariff_period.tariff.name}\n"
                f"⏱️ Термін: {tariff_period.get_months_display()}\n"
                f"💰 Безкоштовно!\n\n"
                "Тепер вам доступні всі функції обраного тарифу!"
            )

            async_to_sync(bot.send_message)(chat_id=user.telegram_id, text=message_text)

        except Exception as e:
            logger.error(
                f"Error sending promo success notification to user {user.telegram_id}: {e}"
            )

    def activate_subscription_from_promo(self, user, promo_code: PromoCode):
        """Activate subscription for a user using a promo code (without payment)"""
        try:
            # Get the tariff period for this promo code
            tariff_period = TariffPeriod.objects.get(
                tariff=promo_code.tariff,
                months=promo_code.months
            )

            # Check if user is trying to downgrade to a lower-tier subscription
            active_subscription = Subscription.objects.filter(
                user=user, is_active=True
            ).select_related('tariff_period__tariff').first()

            if active_subscription:
                current_tariff = active_subscription.tariff_period.tariff
                new_tariff = tariff_period.tariff

                if not new_tariff.is_higher_than(current_tariff) and new_tariff.level != current_tariff.level:
                    logger.warning(
                        f"User {user.telegram_id} attempted to use promo code {promo_code.code} to downgrade from "
                        f"{current_tariff.name} (level {current_tariff.level}) to "
                        f"{new_tariff.name} (level {new_tariff.level}). Promo code rejected."
                    )
                    return None

            # Deactivate all existing active subscriptions
            active_subscriptions = Subscription.objects.filter(
                user=user, is_active=True
            )

            for subscription in active_subscriptions:
                subscription.is_active = False
                subscription.save(update_fields=["is_active"])
                logger.info(
                    f"Deactivated previous subscription {subscription.id} for user {user.telegram_id}"
                )

            # Create new subscription
            start_date = timezone.now()
            end_date = start_date + timedelta(days=tariff_period.months * 30)

            subscription = Subscription.objects.create(
                user=user,
                tariff_period=tariff_period,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
            )

            logger.info(
                f"Activated subscription {subscription.id} for user {user.telegram_id} "
                f"via promo code {promo_code.code} "
                f"({tariff_period.tariff.name} for {tariff_period.months} months)"
            )

            # Send success notification
            self.send_promo_success_notification(user, tariff_period, promo_code)

            return subscription

        except TariffPeriod.DoesNotExist:
            logger.error(
                f"TariffPeriod not found for promo code {promo_code.code}: "
                f"tariff={promo_code.tariff.name}, months={promo_code.months}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Error activating subscription from promo code {promo_code.code} "
                f"for user {user.telegram_id}: {e}",
                exc_info=True,
            )
            return None
