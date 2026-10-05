"""Sanity checks for the tasks.md fixtures used by the manual scenarios."""

import re

TASK = re.compile(r"^- \[[ xX]\] (T\d{3})\b", re.MULTILINE)
PHASE = re.compile(r"^## Phase (\d+): ", re.MULTILINE)


def read(root, name):
    return (root / "tests" / "fixtures" / "tasks" / name).read_text()


def test_s1_counts(root):
    text = read(root, "s1-tasks.md")
    assert len(PHASE.findall(text)) == 3
    assert len(TASK.findall(text)) == 10


def test_large_counts(root):
    text = read(root, "s-large-tasks.md")
    assert len(PHASE.findall(text)) == 6
    ids = TASK.findall(text)
    assert len(ids) == 120
    assert len(set(ids)) == 120


def test_s4_dependencies_reference_known_tasks(root):
    text = read(root, "s4-tasks.md")
    known = set(TASK.findall(text))
    pairs = re.findall(r"^- (T\d{3}) depends on (T\d{3})$", text, re.MULTILINE)
    assert pairs == [("T004", "T002"), ("T005", "T004"), ("T006", "T001")]
    for succ, pred in pairs:
        assert succ in known and pred in known


def test_s4_parallel_tasks_have_no_dependency(root):
    text = read(root, "s4-tasks.md")
    parallel = set(re.findall(r"^- \[ \] (T\d{3}) \[P\]", text, re.MULTILINE))
    assert parallel == {"T001", "T002", "T003"}
    dependents = {s for s, _ in re.findall(r"^- (T\d{3}) depends on (T\d{3})$", text, re.MULTILINE)}
    assert not parallel & dependents
