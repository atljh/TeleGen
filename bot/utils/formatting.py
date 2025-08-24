import re
from html import escape as escape_html
from aiogram.types import Message, MessageEntity


def entity_to_html(entity: MessageEntity, text: str) -> str:
    """
    Convet markdwon type from Telegram to HTML
    """
    if entity.type == "bold":
        return f"<b>{escape_html(text)}</b>"
    elif entity.type == "italic":
        return f"<i>{escape_html(text)}</i>"
    elif entity.type == "underline":
        return f"<u>{escape_html(text)}</u>"
    elif entity.type == "strikethrough":
        return f"<s>{escape_html(text)}</s>"
    elif entity.type == "code":
        return f"<code>{escape_html(text)}</code>"
    elif entity.type == "pre":
        return f"<pre>{escape_html(text)}</pre>"
    elif entity.type == "text_link":
        return f'<a href="{escape_html(entity.url)}">{escape_html(text)}</a>'
    elif entity.type == "url":
        return f'<a href="{escape_html(text)}">{escape_html(text)}</a>'
    else:
        return escape_html(text)


def parse_entities_to_html(message: Message) -> str:

    text = message.text or message.caption or ""
    entities = message.entities or message.caption_entities or []

    if not entities:
        return escape_html(text)

    html_parts = []
    last_offset = 0

    for entity in entities:
        if entity.offset > last_offset:
            html_parts.append(escape_html(text[last_offset:entity.offset]))

        entity_text = text[entity.offset:entity.offset + entity.length]
        html_parts.append(entity_to_html(entity, entity_text))
        last_offset = entity.offset + entity.length

    html_parts.append(escape_html(text[last_offset:]))

    return "".join(html_parts).strip()
