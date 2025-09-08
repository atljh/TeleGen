import os
import logging
import requests
from typing import Optional

logger = logging.getLogger()


async def send_telegram_notification(
    bot_token: str, chat_id: int, message: str, parse_mode: Optional[str] = None
) -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        logging.error(f"Помилка відправки сповіщення: {str(e)}")
        return False


async def notify_admins(message: str, parse_mode: Optional[str] = None) -> bool:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    ADMIN_IDS = [int(x) for x in os.getenv("TELEGRAM_ADMIN_IDS", "").split(",") if x]
    for admin_id in ADMIN_IDS:
        payload = {"chat_id": admin_id, "text": message}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Не вдалося сповістити адміна {admin_id}: {str(e)}")
