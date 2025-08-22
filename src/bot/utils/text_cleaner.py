import re

def escape_markdown_v2(text: str) -> str:
    if not text:
        return text

    def escape(text):
        to_escape = r"_[]()~`>#+-=|{}.!\\"
        return ''.join(f"\\{c}" if c in to_escape else c for c in text)

    bold_pattern = r"\*\*[^\*]+\*\*"
    link_pattern = r"\[[^\]]+\]\([^)]+\)"
    combined_pattern = f"({bold_pattern}|{link_pattern})"

    parts = re.split(combined_pattern, text)

    result = []
    for part in parts:
        if not part:
            continue
        if re.fullmatch(bold_pattern, part) or re.fullmatch(link_pattern, part):
            result.append(part)
        else:
            result.append(escape(part))

    return ''.join(result)