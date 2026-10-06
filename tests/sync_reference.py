"""Reference implementation of the sync-status decision table (research R1) and the
checkbox edit rule (research R5).

Mirrors the `decision-table` block of extension/commands/sync-status.md. Used only by tests:
the shipped command is a prompt, this file keeps the table executable and checkable.
"""

import re

# One row per line; the prompt block must list exactly these rows (tests/test_prompt_sync.py).
# tc: the box differs from the done-ness of the ledger status (a missing ledger status counts as
# not done). oc: the work package status differs from the ledger status (with a missing ledger
# status: the work package is done).
DECISION_ROWS = [
    "| no | no | none |",
    "| no | yes | box differs from the work package: pull |",
    "| no | yes | box already matches the work package: refresh |",
    "| yes | no | checked, work package not done: push |",
    "| yes | no | open, work package still done: pull, reverted |",
    "| yes | yes | box matches the work package: refresh |",
    "| yes | yes | box differs from the work package: conflict, OpenProject wins |",
]

TASK_LINE = re.compile(r"^(\s*)- \[( |x|X)\] (T\d{3,})\b")


def classify(checked, op_status, base, done, closed=(), in_progress="In progress"):
    """Classify one task that has a ledger entry and an existing work package.

    checked: box state; op_status: status name read now; base: ledger status or None.
    Returns action, labels, the resulting checkbox, the resulting ledger status,
    whether OpenProject is written and whether the ledger changes.
    """
    labels = []
    if base is None:
        labels.append("baseline")
    if op_status == in_progress:
        labels.append("in-progress")
    od = op_status == done
    bd = base == done
    result = {"checkbox": checked, "status": op_status, "writes_op": False}

    if op_status in closed and not od:
        labels.append("closed-not-done")
        action = "info"
    else:
        tc = checked != bd
        oc = od if base is None else op_status != base
        if not tc and not oc:
            action = "refresh" if op_status != base else "none"
        elif tc and not oc:
            if checked:
                action = "push"
                result["status"] = done
                result["writes_op"] = True
            else:
                action = "pull"
                labels.append("reverted")
                result["checkbox"] = True
        elif oc and not tc:
            if checked != od:
                action = "pull"
                result["checkbox"] = od
            else:
                action = "refresh"
        elif checked == od:
            action = "refresh"
        else:
            action = "conflict"
            result["checkbox"] = od

    result["action"] = action
    result["labels"] = sorted(labels)
    result["writes_ledger"] = action in ("push", "pull", "conflict") or (
        action in ("refresh", "info") and result["status"] != base
    )
    return result


def classify_item(task_checked, has_entry, wp_exists, **kwargs):
    """Add the cases without a complete task: orphan, unpublished, stale."""
    if task_checked is None:
        return {"action": "orphan", "labels": [], "writes_ledger": False, "writes_op": False}
    if not has_entry:
        return {"action": "unpublished", "labels": [], "writes_ledger": False, "writes_op": False}
    if not wp_exists:
        return {"action": "stale", "labels": [], "writes_ledger": False, "writes_op": False}
    return classify(task_checked, **kwargs)


def apply_checkbox_edits(text, edits):
    """Set the box of each key in edits (key -> bool); change only the bracket character."""
    lines = text.split("\n")
    seen = {}
    for i, line in enumerate(lines):
        m = TASK_LINE.match(line)
        if m:
            key = m.group(3)
            if key in seen:
                raise ValueError(f"repeated task key {key}")
            seen[key] = i
    for key in edits:
        if key not in seen:
            raise ValueError(f"task key {key} not found")
    for key, want in edits.items():
        i = seen[key]
        m = TASK_LINE.match(lines[i])
        current = m.group(2) in ("x", "X")
        if current == want:
            continue
        pos = m.start(2)
        lines[i] = lines[i][:pos] + ("x" if want else " ") + lines[i][pos + 1 :]
    return "\n".join(lines)
