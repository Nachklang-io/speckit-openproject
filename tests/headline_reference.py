"""Reference implementation of the subject rules (speckit.taskstoissues step 7)."""

import re

MAX_HEADLINE = 70
MAX_SUBJECT = 255


def _group_end(text, start):
    """Index after the balanced `(...)` group starting at `start`, or None if unbalanced."""
    depth = 0
    for i in range(start, len(text)):
        depth += (text[i] == "(") - (text[i] == ")")
        if depth == 0:
            return i + 1
    return None


def strip_leading_groups(text):
    """Drop leading `**(...)**` groups and balanced `(...)` groups; an unbalanced `(` stays."""
    while True:
        text = text.strip()
        if text.startswith("**("):
            end = _group_end(text, 2)
            if end is not None and text.startswith("**", end):
                text = text[end + 2 :]
                continue
        if text.startswith("("):
            end = _group_end(text, 0)
            if end is not None:
                text = text[end:]
                continue
        return text


def _cut(text):
    return re.split(r": |; | \(|\. ", text)[0]


def _cap(text):
    text = text.replace("`", "").strip()
    if len(text) > MAX_HEADLINE:
        head = text[:MAX_HEADLINE]
        text = (head.rsplit(" ", 1)[0] if " " in head else head) + "…"
    return text


def headline(text):
    stripped = strip_leading_groups(text)
    return _cap(_cut(stripped)) or _cap(stripped) or _cap(text)


def cap_subject(subject):
    if len(subject) > MAX_SUBJECT:
        return subject[: MAX_SUBJECT - 1] + "…"
    return subject
