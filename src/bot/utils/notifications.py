import logging
import os

import requests

logger = logging.getLogger()


async def send_telegram_notification(
    bot_token: str, chat_id: int, message: str, parse_mode: str | None = None
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
        logging.error(f"Помилка відправки сповіщення: {e!s}")
        return False


async def notify_admins(message: str, parse_mode: str | None = None) -> bool:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # ADMIN_IDS = [int(x) for x in os.getenv("TELEGRAM_ADMIN_IDS", "").split(",") if x]
    # for admin_id in ADMIN_IDS:
    #     payload = {"chat_id": admin_id, "text": message}
    #     if parse_mode:
    #         payload["parse_mode"] = parse_mode
    #     try:
    #         response = requests.post(url, json=payload, timeout=10)
    #         response.raise_for_status()
    #     except Exception as e:
    #         logger.error(f"Не вдалося сповістити адміна {admin_id}: {e!s}")

    log_channel_id = os.getenv("TELEGRAM_LOG_CHANNEL_ID")
    if log_channel_id:
        try:
            payload = {"chat_id": log_channel_id, "text": message}
            if parse_mode:
                payload["parse_mode"] = parse_mode
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Не вдалося відправити в канал логів: {e!s}")

    return True
