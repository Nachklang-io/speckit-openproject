"""Reference implementation of the sync-docs decision table (research R6) and of the summary
block (research R4, R5, R9).

Mirrors the `decision-table` block of extension/commands/sync-docs.md. Used only by tests:
the shipped command is a prompt, this file keeps the table and the block rules executable.
"""

from urllib.parse import urlsplit

# One row per line; the prompt block must list exactly these rows (tests/test_prompt_sync.py).
# "other attachment" = an attachment with the document's file name whose id is neither the
# ledger's attachment_id nor its pending_delete.
DECISION_ROWS = [
    "| missing | no entry, no attachment | skip |",
    "| missing | entry or attachment present | orphan |",
    "| present | no entry, no attachment | new |",
    "| present | no entry, attachment present | blocked (foreign attachment) |",
    "| present | entry, no attachment | restored |",
    "| present | entry, only the ledger attachment, same hash | unchanged |",
    "| present | entry, only the ledger attachment, other hash | changed |",
    "| present | entry, other attachment present | blocked (ambiguous) |",
]

DOCUMENT_ORDER = ["spec.md", "plan.md", "research.md", "data-model.md"]
BEGIN = "<!-- speckit-docs:begin -->"
END = "<!-- speckit-docs:end -->"
WRAPPER_OPEN = "<user-content>"
WRAPPER_CLOSE = "</user-content>"


class BlockError(ValueError):
    """The summary markers in the description are inconsistent: stop, write nothing."""


def classify(local_hash, entry, attachment_ids):
    """Classify one document.

    local_hash: SHA-256 hex of the file, or None if the file is missing.
    entry: the ledger entry (dict with hash, attachment_id, optional pending_delete) or None.
    attachment_ids: ids of the attachments on the work package that have the document's name.

    Returns {"action", "writes", "cleanup"}. writes is the ordered list of write steps;
    cleanup is None, "delete" (pending_delete still on the work package) or "clear"
    (pending_delete already gone: only the ledger changes).
    """
    pending = entry.get("pending_delete") if entry else None
    cleanup = None
    if pending is not None:
        cleanup = "delete" if pending in attachment_ids else "clear"
    found = set(attachment_ids) - ({pending} if pending is not None else set())

    if local_hash is None:
        if entry is None and not found:
            return {"action": "skip", "writes": [], "cleanup": cleanup}
        return {"action": "orphan", "writes": [], "cleanup": cleanup}
    if entry is None:
        if not found:
            return {"action": "new", "writes": ["upload", "ledger"], "cleanup": cleanup}
        return {
            "action": "blocked",
            "reason": "foreign attachment",
            "writes": [],
            "cleanup": cleanup,
        }
    if not found:
        return {"action": "restored", "writes": ["upload", "ledger"], "cleanup": cleanup}
    if found == {entry["attachment_id"]}:
        if entry["hash"] == local_hash:
            return {"action": "unchanged", "writes": [], "cleanup": cleanup}
        return {
            "action": "changed",
            "writes": ["upload", "ledger", "delete", "ledger"],
            "cleanup": cleanup,
        }
    return {"action": "blocked", "reason": "ambiguous", "writes": [], "cleanup": cleanup}


def run(local_hash, entry, attachments, today, next_id):
    """Apply one run for one document to (ledger entry, attachment ids on the work package).

    Returns (new_entry, new_attachment_ids, plan). Mirrors the order of research R7. Used to
    prove idempotence: a second run on the result writes nothing.
    """
    plan = classify(local_hash, entry, attachments)
    ids = list(attachments)
    new = dict(entry) if entry else None

    if plan["cleanup"] == "delete":
        ids.remove(new["pending_delete"])
    if plan["cleanup"] is not None:
        new.pop("pending_delete")

    action = plan["action"]
    if action in ("new", "restored"):
        ids.append(next_id)
        new = {"hash": local_hash, "attachment_id": next_id, "synced": today}
    elif action == "changed":
        old = new["attachment_id"]
        ids.append(next_id)
        new = {"hash": local_hash, "attachment_id": next_id, "synced": today, "pending_delete": old}
        ids.remove(old)  # delete step
        new.pop("pending_delete")
    return new, ids, plan


def link_path(download_url):
    """The path of an attachment's download URL without scheme and host, or None."""
    if not download_url:
        return None
    parts = urlsplit(download_url)
    return parts.path if parts.path.startswith("/") else None


def render_block(documents, link_paths):
    """Render the summary block (markers included) from the ledger's documents.

    link_paths maps a file name to the path of its attachment, or None for the fallback
    (file name in backticks, no link).
    """
    rows = []
    for name in DOCUMENT_ORDER:
        if name not in documents:
            continue
        doc = documents[name]
        path = link_paths.get(name)
        label = f"[{name}]({path})" if path else f"`{name}`"
        rows.append(f"| {label} | `{doc['hash'][:8]}` | {doc['synced']} |")
    lines = [
        BEGIN,
        "## Design documents (generated)",
        "",
        "| Document | Short hash | Last synced change |",
        "|---|---|---|",
        *rows,
        END,
    ]
    return "\n".join(lines)


def strip_wrapper(description):
    """Remove exactly the outer <user-content> wrapper the server puts around a description."""
    if description.startswith(WRAPPER_OPEN) and description.endswith(WRAPPER_CLOSE):
        return description[len(WRAPPER_OPEN) : -len(WRAPPER_CLOSE)]
    return description


def replace_block(description, block):
    """Replace the summary block or append it once; text outside the markers is kept.

    Raises BlockError for any marker state other than 'both exactly once, begin first' or
    'neither'.
    """
    nb, ne = description.count(BEGIN), description.count(END)
    if nb == 0 and ne == 0:
        if description.strip() == "":
            return block
        return description.rstrip("\n") + "\n\n" + block
    if nb != 1 or ne != 1:
        raise BlockError(f"markers: begin x{nb}, end x{ne}")
    i, j = description.index(BEGIN), description.index(END)
    if j < i:
        raise BlockError("end marker before begin marker")
    return description[:i] + block + description[j + len(END) :]


def description_needs_write(description, block):
    """True if replace_block would change the description (no write otherwise)."""
    return replace_block(description, block) != description
