"""Reference implementation of the parent status roll-up of sync-status (feature 007,
research R2–R5).

Mirrors the `rollup-table` block of extension/commands/sync-status.md. Used only by tests:
the shipped command is a prompt, this file keeps the rule executable and checkable.
"""

# The prompt block lists ROLLUP_ROWS, one blank line, then PARENT_ROWS (tests/test_prompt_sync.py).
ROLLUP_ROWS = [
    "| children | rolled-up status R |",
    "|---|---|",
    "| none (phase without task lines; feature with every phase ignored) | none |",
    "| all finished | done |",
    "| at least one finished or in progress | in progress |",
    "| otherwise | open |",
]
# O: status read in step 6; R: rolled-up status; checks in this order, first match wins.
PARENT_ROWS = [
    "| # | condition | action | label |",
    "|---|---|---|---|",
    "| 2 | work package missing | stale (never recreated) | `stale` |",
    "| 3 | R is none | left alone | `no tasks` |",
    "| 4 | O is `statuses.done` | unchanged (never leaves done) | `stays done` if R is not done |",
    "| 5 | O is closed, not done | left alone | `closed, not done` |",
    "| 6 | O is neither `statuses.open` nor `statuses.in_progress` | left alone | `unmapped status` |",
    "| 7 | O equals R | unchanged | — |",
    "| 8 | otherwise | write R | `roll-up` |",
]

# Task actions of the sync-status task table that never let a task count as finished (FR-012).
# A push that became failed or skipped is action "push" with "push" != "confirmed"; a pull or
# conflict that became failed or skipped keeps the status read in step 6.
NEVER_FINISHED = ("unpublished", "stale", "blocked")


def task_status_after(task, statuses, assume_pushes):
    """Status of a task after the task part of the run (research R3); None counts as open.

    task: {"status": read in step 6, "action": task action,
           "push": "confirmed" | "failed" | "skipped"}.
    assume_pushes: the plan and the dry run treat every planned push as confirmed.
    """
    action = task.get("action", "none")
    if action in NEVER_FINISHED:
        return None
    if action == "push":
        if assume_pushes or task.get("push", "confirmed") == "confirmed":
            return statuses["done"]
        return None
    return task["status"]


def task_state(status, statuses, closed):
    """finished / in progress / open for one task (research R3)."""
    if status is None:
        return "open"
    if status == statuses["done"] or status in closed:
        return "finished"
    if status == statuses["in_progress"]:
        return "in progress"
    return "open"


def rollup(states):
    """The roll-up rule (research R2)."""
    if not states:
        return "none"
    if all(s == "finished" for s in states):
        return "done"
    if any(s in ("finished", "in progress") for s in states):
        return "in progress"
    return "open"


def target_status(r, statuses):
    return {
        "done": statuses["done"],
        "in progress": statuses["in_progress"],
        "open": statuses["open"],
    }[r]


def status_state(status, statuses, closed):
    """Contribution of a parent status to the feature (research R5)."""
    if status == statuses["done"] or status in closed:
        return "finished"
    if status == statuses["open"]:
        return "open"
    return "in progress"  # statuses.in_progress or an unmapped open status such as On hold


def classify_parent(op_status, r, statuses, closed, exists, base=None):
    """Parent decision (research R4). Returns row, action, label and the refreshed ledger status.

    `ledger` is the status the ledger gets without a write (None: unchanged); a row-8 parent
    gets R after its confirmed write.
    """
    if not exists:
        return {"row": 2, "action": "stale", "label": "stale", "ledger": None}
    ledger = op_status if base != op_status else None
    if r == "none":
        row, action, label = 3, "left alone", "no tasks"
    elif op_status == statuses["done"]:
        row, action, label = 4, "unchanged", None if r == "done" else "stays done"
    elif op_status in closed:
        row, action, label = 5, "left alone", "closed, not done"
    elif op_status not in (statuses["open"], statuses["in_progress"]):
        row, action, label = 6, "left alone", "unmapped status"
    elif op_status == target_status(r, statuses):
        row, action, label = 7, "unchanged", None
    else:
        row, action, label = 8, "roll-up", "roll-up"
    return {"row": row, "action": action, "label": label, "ledger": ledger}


def phase_contribution(result, op_status, r, statuses, closed, fresh=None):
    """State a handled parent contributes to the feature (research R5); None = ignored."""
    action = result["action"]
    if result.get("label") in ("no tasks", "no heading", "unpublished phase"):
        return None
    if action == "stale":
        return None if r == "none" else ("open" if r == "open" else "in progress")
    if action in ("rolled up", "roll-up"):
        return {"done": "finished", "in progress": "in progress", "open": "open"}[r]
    if action == "failed":
        return status_state(fresh if fresh is not None else op_status, statuses, closed)
    return status_state(op_status, statuses, closed)


def feature_rollup(contributions):
    return rollup([c for c in contributions if c is not None])


def phase_number(key):
    return int(key.split("-", 1)[1])


def _handle(parent, planned_r, actual_r, ctx):
    """Plan, then step 14 for one parent. Returns the result dict and the fresh read (if any)."""
    statuses, closed = ctx["statuses"], ctx["closed"]
    op_status = parent.get("O")
    res = classify_parent(
        op_status, planned_r, statuses, closed, parent.get("exists", True), parent.get("B")
    )
    res["R"] = planned_r
    res["writes_op"] = False
    fresh = None
    actual = classify_parent(
        op_status, actual_r, statuses, closed, parent.get("exists", True), parent.get("B")
    )
    planned_write = res["row"] == 8
    if planned_write and parent.get("preview") == "blocked":
        res.update(action="blocked", label="blocked")
    elif ctx["dry_run"]:
        pass
    elif ctx["task_part_stopped"]:
        if planned_write:
            res.update(action="skipped", label="task part stopped")
    elif (planned_write and actual_r != planned_r) or (not planned_write and actual["row"] == 8):
        res.update(action="skipped", label="plan changed")
    elif planned_write:
        recheck = parent.get("recheck", op_status)
        if recheck != op_status:
            res.update(action="failed", label="changed meanwhile", ledger=None)
            fresh = recheck
        elif parent.get("write", "confirmed") == "confirmed":
            res.update(action="rolled up", ledger=target_status(planned_r, statuses))
            res["writes_op"] = True
        else:
            res.update(action="failed", label="unconfirmed write", ledger=None)
            fresh = parent.get("fresh_read")
    return res, fresh


def run_rollup(case):
    """Plan and apply the roll-up of one fixture case (steps 7, 8, 14 and 15).

    Returns {"parents": {key: result}, "closed_tasks": {phase key: [task keys]}}; with the
    switch off, no parent is handled at all.
    """
    statuses, closed = case["statuses"], tuple(case.get("closed", ()))
    if case.get("rollup_parents", True) is False:
        return {"parents": {}, "closed_tasks": {}}
    ctx = {
        "statuses": statuses,
        "closed": closed,
        "dry_run": case.get("dry_run", False),
        "task_part_stopped": case.get("task_part_stopped", False),
    }
    parents, closed_tasks, order = {}, {}, []
    planned_c, actual_c = [], []
    for phase in sorted(case.get("phases", []), key=lambda p: phase_number(p["key"])):
        key = phase["key"]
        order.append(key)
        if not phase.get("heading", True):
            parents[key] = {"action": "left alone", "label": "no heading", "ledger": None}
            continue
        if not phase.get("ledger", True):
            parents[key] = {"action": "left alone", "label": "unpublished phase", "ledger": None}
            continue
        tasks = phase.get("tasks", [])
        planned = [
            task_state(task_status_after(t, statuses, True), statuses, closed) for t in tasks
        ]
        actual_s = [task_status_after(t, statuses, ctx["dry_run"]) for t in tasks]
        actual = [task_state(s, statuses, closed) for s in actual_s]
        names = [
            t["key"]
            for t, s in zip(tasks, actual_s, strict=True)
            if s is not None and s in closed and s != statuses["done"]
        ]
        if names:
            closed_tasks[key] = names
        planned_r, actual_r = rollup(planned), rollup(actual)
        res, fresh = _handle(phase, planned_r, actual_r, ctx)
        parents[key] = res
        plan_res = (
            dict(res, action="roll-up") if res["row"] == 8 and res["action"] != "blocked" else res
        )
        planned_c.append(phase_contribution(plan_res, phase.get("O"), planned_r, statuses, closed))
        actual_c.append(
            phase_contribution(res, phase.get("O"), actual_r, statuses, closed, fresh)
            if res["action"] != "skipped"
            else status_state(phase.get("O"), statuses, closed)
        )
    feature = case.get("feature")
    if feature is not None:
        res, _ = _handle(feature, feature_rollup(planned_c), feature_rollup(actual_c), ctx)
        parents["feature"] = res
        order.append("feature")
    return {"parents": parents, "closed_tasks": closed_tasks, "order": order}


def phase_key(number):
    """Ledger key of a `## Phase N` heading: N without leading zeros (preset and sync-status)."""
    return f"phase-{int(number)}"


def assign_phases(tasks, ledger_phases):
    """Phase membership of task lines (FR-002, review follow-up).

    tasks: [{"key", "heading": phase key of the nearest heading above or None,
             "parent_id": parent read in step 6 or None (no parent, not read)}].
    ledger_phases: {phase key: {"id": work package id, "heading": has a `## Phase N` heading}}.
    Returns ({task key: phase key or None}, [report lines]).
    """
    by_id = {p["id"]: key for key, p in ledger_phases.items()}
    phases, lines = {}, []
    for task in tasks:
        key, heading = task["key"], task.get("heading")
        parent = by_id.get(task.get("parent_id"))
        if parent is None:
            phases[key] = heading
            continue
        if not ledger_phases[parent].get("heading", True):
            phases[key] = None
            lines.append(f"{key} not counted: its parent {parent} has no heading")
            continue
        phases[key] = parent
        if parent != heading:
            where = f"under heading {heading}" if heading else "above the first heading"
            lines.append(f"{key} counted for {parent} (parent in OpenProject), {where}")
    return phases, lines
