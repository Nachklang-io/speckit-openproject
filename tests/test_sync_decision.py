import json

import pytest
from conftest import ROOT
from sync_reference import apply_checkbox_edits, classify, classify_item

DONE = "Closed"


DATA = json.loads((ROOT / "tests/fixtures/sync/decision-table.json").read_text())


def pytest_generate_tests(metafunc):
    if "case" in metafunc.fixturenames:
        metafunc.parametrize("case", DATA["cases"], ids=[c["name"] for c in DATA["cases"]])
    if "item" in metafunc.fixturenames:
        metafunc.parametrize("item", DATA["items"], ids=[c["name"] for c in DATA["items"]])


def run(case):
    return classify(case["checked"], case["op_status"], case["base"], case["done"], case["closed"])


def test_every_row_of_the_table(case):
    got = run(case)
    for key, want in case["expect"].items():
        assert got[key] == want, f"{key}: {got}"


def test_items_without_a_complete_task(item):
    got = classify_item(
        item["task_checked"],
        item["has_entry"],
        item["wp_exists"],
        op_status="New",
        base="New",
        done=DONE,
    )
    assert got["action"] == item["expect"]
    assert not got["writes_op"]


def test_second_run_changes_nothing(case):
    first = run(case)
    op_after = DONE if first["writes_op"] else case["op_status"]
    second = classify(first["checkbox"], op_after, first["status"], case["done"], case["closed"])
    assert second["action"] == "none", (first, second)
    assert not second["writes_ledger"]
    assert not second["writes_op"]
    assert second["checkbox"] == first["checkbox"]


def test_baseline_never_conflicts():
    for checked in (True, False):
        for op in ("New", "In progress", DONE, "Rejected", "On hold"):
            got = classify(checked, op, None, DONE, ["Closed", "Rejected"])
            assert got["action"] != "conflict"
            assert "baseline" in got["labels"]


def test_closed_not_done_never_pushes_or_changes_the_box():
    for checked in (True, False):
        got = classify(checked, "Rejected", "New", DONE, ["Closed", "Rejected"])
        assert not got["writes_op"]
        assert got["checkbox"] == checked


def test_done_work_package_is_never_reopened_by_a_push():
    for checked in (True, False):
        for base in (None, "New", DONE):
            got = classify(checked, DONE, base, DONE, ["Closed", "Rejected"])
            assert not got["writes_op"]


TASKS = """# Tasks: Demo

## Phase 1: Setup

- [ ] T001 Create skeleton in src/app/__init__.py
- [X] T002 [P] Add loader in `src/app/config.py`  
  - [ ] T002a not a task line (indented sub item without key match)
- [ ] T010 [US1] Done when - [ ] T001 is mentioned in text
Text with [ ] and T001 in prose.
"""


def changed_positions(a, b):
    assert len(a) == len(b)
    return [i for i, (x, y) in enumerate(zip(a, b, strict=True)) if x != y]


def test_checkbox_edit_changes_only_bracket_characters():
    out = apply_checkbox_edits(TASKS, {"T001": True, "T002": False})
    pos = changed_positions(TASKS, out)
    assert len(pos) == 2
    assert all(TASKS[i] in " xX" and out[i] in " x" for i in pos)
    assert out.splitlines()[4].startswith("- [x] T001")
    assert out.splitlines()[5].startswith("- [ ] T002 [P]")
    assert out.splitlines()[5].endswith("config.py`  ")


def test_checkbox_edit_keeps_capital_x_when_the_box_stays_checked():
    assert apply_checkbox_edits(TASKS, {"T002": True}) == TASKS


def test_checkbox_edit_without_edits_is_identical():
    assert apply_checkbox_edits(TASKS, {}) == TASKS


def test_checkbox_edit_rejects_repeated_and_unknown_keys():
    with pytest.raises(ValueError):
        apply_checkbox_edits(TASKS + "- [ ] T001 again\n", {"T001": True})
    with pytest.raises(ValueError):
        apply_checkbox_edits(TASKS, {"T099": True})
