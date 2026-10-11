"""The parent status roll-up of sync-status (feature 007) against tests/rollup_reference.py."""

import copy
import json
from pathlib import Path

import pytest
from rollup_reference import assign_phases, phase_key, run_rollup

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "sync" / "rollup-cases.json").read_text(encoding="utf-8")
)
CASES = [
    dict(case, statuses=FIXTURE["statuses"], closed=FIXTURE["closed"]) for case in FIXTURE["cases"]
]


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_rollup_case(case):
    result = run_rollup(case)
    got = {key: [res["action"], res.get("label")] for key, res in result["parents"].items()}
    assert got == case["expect"]
    for key, r in case.get("expect_R", {}).items():
        assert result["parents"][key]["R"] == r, key
    for key, ledger in case.get("expect_ledger", {}).items():
        assert result["parents"][key]["ledger"] == ledger, key
    if "expect_closed_tasks" in case:
        assert result["closed_tasks"] == case["expect_closed_tasks"]
    if "expect_order" in case:
        assert result["order"] == case["expect_order"]


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_done_parent_is_never_written(case):
    result = run_rollup(case)
    parents = {p["key"]: p for p in case.get("phases", [])}
    if "feature" in case:
        parents["feature"] = case["feature"]
    for key, res in result["parents"].items():
        if parents[key].get("O") == case["statuses"]["done"]:
            assert res["action"] not in ("roll-up", "rolled up"), key


def second_run(case, result):
    """The same case after the first run: written parents carry R, pushed tasks are done."""
    nxt = copy.deepcopy(case)
    done = case["statuses"]["done"]
    for key, res in result["parents"].items():
        parent = (
            nxt["feature"]
            if key == "feature"
            else next(p for p in nxt["phases"] if p["key"] == key)
        )
        if res["action"] == "rolled up":
            parent["O"] = res["ledger"]
        for field in ("preview", "recheck", "write", "fresh_read"):
            parent.pop(field, None)
        parent["B"] = parent.get("O")
    for phase in nxt.get("phases", []):
        for task in phase.get("tasks", []):
            if task.get("action") == "push" and task.get("push", "confirmed") == "confirmed":
                task.update(status=done, action="none")
    return nxt


IDEMPOTENT = [c for c in CASES if not c.get("dry_run") and not c.get("task_part_stopped")]


@pytest.mark.parametrize("case", IDEMPOTENT, ids=[c["name"] for c in IDEMPOTENT])
def test_second_run_writes_nothing(case):
    first = run_rollup(case)
    if not any(res["action"] == "rolled up" for res in first["parents"].values()):
        return
    again = run_rollup(second_run(case, first))
    written = [
        k for k, res in again["parents"].items() if res["action"] in ("rolled up", "roll-up")
    ]
    # A parent skipped in the first run (plan changed) may be written now; every written one is not.
    skipped = {k for k, res in first["parents"].items() if res["action"] in ("skipped", "failed")}
    assert set(written) <= skipped


def test_switch_off_handles_no_parent():
    case = next(c for c in CASES if c.get("rollup_parents") is False)
    assert run_rollup(case) == {"parents": {}, "closed_tasks": {}}
    assert run_rollup(dict(case, rollup_parents=True))["parents"]


MEMBERSHIP = FIXTURE["membership"]


@pytest.mark.parametrize("case", MEMBERSHIP, ids=[c["name"] for c in MEMBERSHIP])
def test_membership_case(case):
    phases, lines = assign_phases(case["tasks"], case["phases"])
    assert phases == case["expect"]
    assert lines == case["expect_lines"]


@pytest.mark.parametrize(
    ("number", "key"), [("1", "phase-1"), ("01", "phase-1"), ("007", "phase-7")]
)
def test_phase_key_strips_zeros(number, key):
    assert phase_key(number) == key
