import json
import logging

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .services import PaymentHandler

logger = logging.getLogger(__name__)
payment_handler = PaymentHandler()


@csrf_exempt
def monobank_webhook(request):
    if request.method == "GET":
        return HttpResponse("OK", status=200)

    if request.method == "POST":
        try:
            body = request.body.decode("utf-8")
            data = json.loads(body)
            logger.info(f"Monobank webhook: {data}")

            payment_handler.handle_monobank_webhook(data)

            return JsonResponse({"status": "ok"})
        except Exception as e:
            logger.error(f"Monobank webhook error: {e}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def cryptobot_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        logger.info(f"CryptoBot webhook: {data}")

        payment_handler.handle_cryptobot_webhook(data)

        return JsonResponse({"status": "ok"})
    except Exception as e:
        logger.error(f"CryptoBot webhook error: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=400)
