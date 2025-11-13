import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# Store message_ids per user: {user_id: [message_ids]}
_user_messages: dict[int, list[int]] = defaultdict(list)


def save_message_ids(user_id: int, message_ids: list[int]) -> None:
    _user_messages[user_id] = message_ids
    logger.info(f"Saved {len(message_ids)} message_ids for user {user_id}: {message_ids}")


def get_message_ids(user_id: int) -> list[int]:
    message_ids = _user_messages.get(user_id, [])
    logger.info(f"Retrieved {len(message_ids)} message_ids for user {user_id}: {message_ids}")
    return message_ids


def clear_message_ids(user_id: int) -> None:
    if user_id in _user_messages:
        count = len(_user_messages[user_id])
        del _user_messages[user_id]
        logger.info(f"Cleared {count} message_ids for user {user_id}")
