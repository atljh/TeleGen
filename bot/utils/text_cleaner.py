import re

def escape_markdown_v2(text: str) -> str:
    if not text:
        return text
    def escape(text):
        to_escape = r"_*[]()~`>#+-=|{}.!\\"
        return ''.join(f"\\{char}" if char in to_escape else char for char in text)

    parts = re.split(r"(\[[^\]]+\]\([^)]+\))", text)
    return ''.join(escape(part) if not part.startswith("[") else part for part in parts)
