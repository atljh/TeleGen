import logging

from admin_panel.admin_panel.models import Payment

logger = logging.getLogger(__name__)


class PaymentHandler:
    def handle_monobank_webhook(self, data: dict):
        invoice = data.get("invoice", {})
        reference = invoice.get("reference")
        status = invoice.get("status")

        if not reference:
            logger.warning("No reference in Monobank webhook")
            return

        try:
            payment = Payment.objects.get(id=reference)
        except Payment.DoesNotExist:
            logger.error(f"Payment with id={reference} not found")
            return

        if status == "success":
            payment.is_successful = True
            payment.save(update_fields=["is_successful"])
            logger.info(f"Payment {payment.id} marked as successful")

    def handle_cryptobot_webhook(self, data: dict):
        payload = data.get("payload", {})
        invoice_id = payload.get("invoice_id")
        status = payload.get("status")

        if not invoice_id:
            logger.warning("No invoice_id in CryptoBot webhook")
            return

        try:
            payment = Payment.objects.get(id=invoice_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment with id={invoice_id} not found")
            return

        if status == "paid":
            payment.is_successful = True
            payment.save(update_fields=["is_successful"])
            logger.info(f"Payment {payment.id} marked as successful")
