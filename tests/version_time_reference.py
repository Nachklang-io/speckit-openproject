"""Reference implementation of the version decision tables (research R3), the duration
grammar (research R5), the time-entry key (research R6) and the time-entry plan
classification (research R3/R6/R8 combined).

Mirrors the `decision-table` block of extension/commands/sync-version.md and the
`duration-grammar` block of extension/commands/log-time.md. Used only by tests: the shipped
commands are prompts, this file keeps the tables and the grammar executable and checkable.
"""

import re
from datetime import date

# One row per line; the sync-version.md decision-table block must list exactly these rows
# (tests/test_prompt_sync.py), in this order: first the version-level table (L = ledger
# version, M = matching project versions), then the per-work-package table (W = the work
# package's current version, read back from get_work_package as a NAME, never an id - R1).
VERSION_DECISION_ROWS = [
    "| none | empty | create | create_version, ledger |",
    "| none | one (open) | reuse | ledger |",
    "| none | one (closed or locked) | closed / locked (stop for assignment) | none |",
    "| none | several | blocked (ambiguous name) | none |",
    "| id | found (open) | use it; name differs from intended: warning, id wins | none |",
    "| id | found (closed or locked) | closed / locked (stop for assignment) | none |",
    "| id | not found | stale (stop, name the ledger entry) | none |",
]

WORK_PACKAGE_DECISION_ROWS = [
    "| = V (by name) | unchanged | none |",
    "| none | assign | update (bulk) |",
    "| other | other version (reported, never moved) | none |",
    "| not found | stale, skip | none |",
]

DECISION_ROWS = VERSION_DECISION_ROWS + WORK_PACKAGE_DECISION_ROWS


def classify_version(ledger_version, matches, status):
    """Classify the feature's version against the project (research R3, version-level table).

    ledger_version: None, or the ledger's {"id", "name"}.
    matches: candidate versions in the project, each {"id", "name"} - *all* versions whose
        name equals the intended name when ledger_version is None (a `list-versions` search),
        or the single version found by `get-version(ledger_version["id"])` (0 or 1 item) when
        ledger_version is given.
    status: the status ("open", "closed", "locked") of the chosen candidate - the single
        match when len(matches) == 1 - or None when no candidate is chosen yet (create,
        blocked, stale; status is ignored in those cases).

    Returns a dict with "action" (create, reuse, blocked, stale, closed, locked, use) and
    "writes" (the list of write steps), plus "id"/"name" of the chosen version and an
    optional "warning" when relevant.
    """
    if ledger_version is None:
        if len(matches) == 0:
            return {"action": "create", "writes": ["create_version", "ledger"]}
        if len(matches) > 1:
            return {"action": "blocked", "writes": [], "reason": "ambiguous name"}
        chosen = matches[0]
        if status in ("closed", "locked"):
            return {"action": status, "writes": [], "id": chosen["id"], "name": chosen["name"]}
        return {"action": "reuse", "writes": ["ledger"], "id": chosen["id"], "name": chosen["name"]}

    if not matches:
        return {"action": "stale", "writes": []}
    chosen = matches[0]
    result = {"id": chosen["id"], "name": chosen["name"]}
    if status in ("closed", "locked"):
        result.update(action=status, writes=[])
        return result
    result.update(action="use", writes=[])
    if chosen["name"] != ledger_version["name"]:
        result["warning"] = "name differs from the ledger entry; id wins"
    return result


def classify_work_package(wp_version, version_name, exists):
    """Classify one ledger work package against the chosen version (R3, per-work-package table).

    wp_version: the work package's current version NAME (string) or None, as read back from
        `get_work_package` (R1: the `version` field is always a name, never an id).
    version_name: the chosen version's name (V in R3).
    exists: whether `get_work_package` found the work package at all.

    Returns a dict with "action" (unchanged, assign, other, stale) and "writes".
    """
    if not exists:
        return {"action": "stale", "writes": []}
    if wp_version is None:
        return {"action": "assign", "writes": ["update"]}
    if wp_version == version_name:
        return {"action": "unchanged", "writes": []}
    return {"action": "other", "writes": [], "current": wp_version}


# --- Duration grammar (research R5) -----------------------------------------------------

# One form per line; the log-time.md duration-grammar block must list exactly these forms
# (accepted, then rejected), in this order (tests/test_prompt_sync.py).
ACCEPTED_DURATION_FORMS = ["1h30", "1h30m", "1:30", "90m", "45m", "1.5h", "2h"]
REJECTED_DURATION_FORMS = [
    "0m",
    "-1h",
    "25h",
    "1.505h",
    "abc",
    "",
    "2026-13-01",
    "<date in the future>",
    "07.10.2026",
]

_HM = re.compile(r"^(\d+)h(\d+)m?$")
_COLON = re.compile(r"^(\d+):(\d+)$")
_M = re.compile(r"^(\d+)m$")
_H = re.compile(r"^(\d+(?:\.\d+)?)h$")
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_LINE = re.compile(r"^(\S+):\s*(.+)$")
_ON_DATE = re.compile(r"\s+on\s+(\S+)$")


def _parse_duration(text):
    """Minutes for one duration token, or None if it does not match any accepted form."""
    text = text.strip()
    for pattern, handler in (
        (_HM, lambda m: int(m.group(1)) * 60 + int(m.group(2))),
        (_COLON, lambda m: int(m.group(1)) * 60 + int(m.group(2))),
        (_M, lambda m: int(m.group(1))),
    ):
        m = pattern.match(text)
        if m:
            return handler(m)
    m = _H.match(text)
    if m:
        minutes = float(m.group(1)) * 60
        if minutes != int(minutes):
            return None  # fraction of a minute, e.g. 1.505h -> 90.3
        return int(minutes)
    return None


def _is_calendar_date(text):
    try:
        date.fromisoformat(text)
        return True
    except ValueError:
        return False


def parse_line(text, today):
    """Parse one `<task key>: <duration> [on <YYYY-MM-DD>]` line (research R5).

    today: "YYYY-MM-DD", the fallback date (R9: from the shell, never guessed by the model).

    Returns {"key", "minutes", "date"} on success, or a rejection reason (str) otherwise.
    Does not split on ';' or newline - the caller splits a run's input into lines first.
    """
    text = text.strip()
    if not text:
        return "empty line"
    m = _LINE.match(text)
    if not m:
        return "missing ': <duration>'"
    key, rest = m.group(1), m.group(2).strip()

    result_date = today
    dm = _ON_DATE.search(rest)
    if dm:
        date_text = dm.group(1)
        rest = rest[: dm.start()].strip()
        if not _ISO_DATE.match(date_text):
            return "date not in YYYY-MM-DD format"
        if not _is_calendar_date(date_text):
            return "not a calendar date"
        if date_text > today:
            return "date in the future"
        result_date = date_text

    minutes = _parse_duration(rest)
    if minutes is None:
        return "unparsable duration"
    if minutes <= 0:
        return "zero or negative duration"
    if minutes > 24 * 60:
        return "duration over 24h"
    return {"key": key, "minutes": minutes, "date": result_date}


def to_iso(minutes):
    """Whole minutes -> ISO 8601 duration, zero parts dropped (PT1H30M, PT45M, PT2H)."""
    hours, mins = divmod(minutes, 60)
    text = "PT"
    if hours:
        text += f"{hours}H"
    if mins:
        text += f"{mins}M"
    if text == "PT":
        text += "0M"
    return text


# --- Time-entry key and plan classification (research R6, R8) ---------------------------


def entry_key(work_package_id, spent_on, activity, iso, entry_key=None):
    """The ledger `time_entries` key for one logged line (research R6).

    `entry_key` (the argument) is `--entry-key <k>` when given; it only applies to a run with
    exactly one item (checked by the prompt, not here) and overrides the computed key.
    """
    if entry_key is not None:
        return f"entry:{entry_key}"
    return f"{work_package_id}|{spent_on}|{activity}|{iso}"


def classify_time(item, ledger_time_entries):
    """Classify one parsed, resolved time-log line (research R6, R8).

    item: {"key": <computed ledger key>, "rejected": reason or None, "known": bool
        (the task key or #<id> is in the ledger), "exists": bool (get_work_package found it)}.
    ledger_time_entries: the ledger's existing `time_entries` (list of dicts with "key").

    Returns one of: create, unchanged, unknown, rejected, stale.
    """
    if item.get("rejected"):
        return "rejected"
    if not item.get("known", True):
        return "unknown"
    if not item.get("exists", True):
        return "stale"
    existing = {e["key"] for e in ledger_time_entries}
    if item["key"] in existing:
        return "unchanged"
    return "create"
