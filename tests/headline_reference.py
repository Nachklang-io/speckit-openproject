"""Reference implementation of the subject rules (speckit.taskstoissues step 7)."""

import re

MAX_HEADLINE = 70
MAX_SUBJECT = 255
PREPOSITIONS = ("in", "at", "to", "for", "from", "into", "under")
# The file hint: the first token with a `/`, or ending in `.ext` (letter first, 2+ chars before).
_FILE_HINT = re.compile(
    r"`?(?:\S*/\S*?|[\w./-]{2,}\.[A-Za-z][A-Za-z0-9]{0,4})`?(?=[.,:;]?(?:\s|$))"
)


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
        text = (head.rsplit(" ", 1)[0].rstrip() if " " in head else head) + "…"
    return text


def drop_file_hint(text):
    """Remove the file hint (first path) only together with the preposition directly before it."""
    for token in re.finditer(r"\S+", text):
        hint = _FILE_HINT.match(token.group())
        if hint is None:
            continue
        before = text[: token.start()]
        words = before.rstrip().rsplit(" ", 1)
        if before.endswith(" ") and len(words) == 2 and words[1] in PREPOSITIONS:
            return words[0] + text[token.start() + hint.end() :]
        return text
    return text


def headline(text):
    text = drop_file_hint(text)
    stripped = strip_leading_groups(text)
    return _cap(_cut(stripped)) or _cap(stripped) or _cap(text)


def cap_subject(subject):
    if len(subject) > MAX_SUBJECT:
        return subject[: MAX_SUBJECT - 1] + "…"
    return subject
