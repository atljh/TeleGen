import hashlib
import hmac
import json

from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def monobank_webhook(request):
    if request.method != "POST":
        return HttpResponseForbidden("Method not allowed")

    received_token = request.headers.get("X-Token")
    expected_token = getattr(settings, "MONOBANK_WEBHOOK_TOKEN", None)

    if expected_token and received_token != expected_token:
        return HttpResponseForbidden("Invalid token")

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseForbidden("Invalid JSON")

    invoice_id = payload.get("invoiceId")
    status = payload.get("status")

    print(f"[Monobank] Invoice {invoice_id} status={status}")

    return JsonResponse({"ok": True})


@csrf_exempt
def cryptobot_webhook(request):
    if request.method != "POST":
        return HttpResponseForbidden("Method not allowed")

    signature = request.headers.get("X-Crypto-Pay-Signature")
    secret = getattr(settings, "CRYPTOBOT_WEBHOOK_SECRET", None)

    body = request.body.decode("utf-8")

    if secret:
        expected_sig = hmac.new(
            key=secret.encode(), msg=body.encode(), digestmod=hashlib.sha256
        ).hexdigest()

        if signature != expected_sig:
            return HttpResponseForbidden("Invalid signature")

    try:
        payload = json.loads(body)
    except Exception:
        return HttpResponseForbidden("Invalid JSON")

    invoice_id = payload.get("payload", {}).get("invoice_id")
    status = payload.get("status")

    print(f"[CryptoBot] Invoice {invoice_id} status={status}")

    return JsonResponse({"ok": True})
