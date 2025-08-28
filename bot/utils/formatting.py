import re
from html import escape as escape_html
from aiogram.types import Message, MessageEntity


def entity_to_html(entity: MessageEntity, text: str) -> str:

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

    chars = []
    for i in range(len(text)):
        char_formats = []
        for entity in entities:
            if entity.offset <= i < entity.offset + entity.length:
                char_formats.append(entity.type)
        chars.append({
            'char': text[i],
            'formats': char_formats
        })

    html_parts = []
    current_formats = []
    current_text = ""

    for char_info in chars:
        if char_info['formats'] == current_formats:
            current_text += char_info['char']
        else:
            if current_text:
                html_parts.append(apply_formats(current_text, current_formats, entities))
            current_text = char_info['char']
            current_formats = char_info['formats']

    if current_text:
        html_parts.append(apply_formats(current_text, current_formats, entities))

    return "".join(html_parts).strip()


def apply_formats(text: str, formats: list, all_entities: list) -> str:
    if not formats:
        return escape_html(text)

    format_priority = ['text_link', 'url', 'bold', 'italic', 'underline', 'strikethrough', 'code', 'pre']
    formats_sorted = sorted(formats, key=lambda x: format_priority.index(x) if x in format_priority else 999)

    formatted_text = escape_html(text)
    
    for fmt in reversed(formats_sorted):
        if fmt == 'bold':
            formatted_text = f"<b>{formatted_text}</b>"
        elif fmt == 'italic':
            formatted_text = f"<i>{formatted_text}</i>"
        elif fmt == 'underline':
            formatted_text = f"<u>{formatted_text}</u>"
        elif fmt == 'strikethrough':
            formatted_text = f"<s>{formatted_text}</s>"
        elif fmt == 'code':
            formatted_text = f"<code>{formatted_text}</code>"
        elif fmt == 'pre':
            formatted_text = f"<pre>{formatted_text}</pre>"
        elif fmt == 'text_link':
            url = None
            for entity in all_entities:
                if entity.type == 'text_link' and entity.offset <= text.find(text[0]) < entity.offset + entity.length:
                    url = entity.url
                    break
            if url:
                formatted_text = f'<a href="{escape_html(url)}">{formatted_text}</a>'
        elif fmt == 'url':
            formatted_text = f'<a href="{escape_html(text)}">{formatted_text}</a>'

    return formatted_text