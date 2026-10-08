"""Reference implementation of the task headline rule (speckit.taskstoissues step 7)."""

import re

MAX_HEADLINE = 70


def strip_leading_groups(text):
    """Drop leading `**(...)**` groups and balanced `(...)` groups."""
    while True:
        text = text.strip()
        m = re.match(r"^\*\*\(.*?\)\*\*\s*", text)
        if m:
            text = text[m.end() :]
            continue
        if text.startswith("("):
            depth = 0
            for i, c in enumerate(text):
                depth += (c == "(") - (c == ")")
                if depth == 0:
                    text = text[i + 1 :]
                    break
            else:
                return text
            continue
        return text


def _cut(text):
    return re.split(r":\s|;\s|\s\(|\.\s", text)[0]


def _cap(text):
    text = text.replace("`", "").strip()
    if len(text) > MAX_HEADLINE:
        head = text[:MAX_HEADLINE]
        text = (head.rsplit(" ", 1)[0] if " " in head else head) + "\u2026"
    return text


def headline(text):
    stripped = strip_leading_groups(text)
    return _cap(_cut(stripped)) or _cap(stripped)
