"""Decision table and summary block of the sync-docs command, against fixtures."""

import json
import re

import pytest
from docs_reference import (
    BEGIN,
    END,
    BlockError,
    classify,
    description_needs_write,
    link_path,
    render_block,
    replace_block,
    run,
    strip_wrapper,
)

TODAY = "2026-10-06"


@pytest.fixture(scope="module")
def table(root):
    return json.loads((root / "tests/fixtures/docs/decision-table.json").read_text())


def fixture_text(root, name):
    return (root / "tests/fixtures/docs" / name).read_text()


def test_every_case_of_the_decision_table(table):
    for case in table["cases"]:
        result = classify(case["local"], case["entry"], case["attachments"])
        assert result["action"] == case["action"], case["name"]
        assert result["writes"] == case["writes"], case["name"]
        assert result["cleanup"] == case["cleanup"], case["name"]
        if "reason" in case:
            assert result["reason"] == case["reason"], case["name"]


def test_blocked_documents_never_write(table):
    for case in table["cases"]:
        if case["action"] in ("blocked", "orphan", "skip", "unchanged"):
            assert case["writes"] == [], case["name"]


def test_second_run_writes_nothing(table):
    """Idempotence (SC-002): after a run, the same input yields no write for every document."""
    for case in table["cases"]:
        if case["action"] in ("blocked", "orphan", "skip"):
            continue
        entry, attachments, _plan = run(
            case["local"], case["entry"], case["attachments"], TODAY, 99
        )
        again = classify(case["local"], entry, attachments)
        assert again["action"] == "unchanged", case["name"]
        assert again["writes"] == [] and again["cleanup"] is None, case["name"]


def test_changed_leaves_exactly_one_attachment_with_the_new_id(table):
    entry = {"hash": table["hash_1"], "attachment_id": 4, "synced": "2026-10-01"}
    new, ids, plan = run(table["hash_2"], entry, [4], TODAY, 7)
    assert plan["action"] == "changed"
    assert ids == [7]
    assert new == {"hash": table["hash_2"], "attachment_id": 7, "synced": TODAY}


def test_interrupted_run_is_finished_without_duplicates(table):
    entry = {
        "hash": table["hash_2"],
        "attachment_id": 6,
        "synced": TODAY,
        "pending_delete": 5,
    }
    new, ids, plan = run(table["hash_2"], entry, [5, 6], TODAY, 99)
    assert plan["cleanup"] == "delete"
    assert ids == [6]
    assert "pending_delete" not in new


def test_unknown_attachment_is_never_deleted(table):
    """Only the ledger's own ids are ever deleted (ADR-0004)."""
    entry = {"hash": table["hash_1"], "attachment_id": 4, "synced": "2026-10-01"}
    for attachments in ([4, 9], [9]):
        new, ids, plan = run(table["hash_2"], entry, attachments, TODAY, 99)
        assert plan["action"] == "blocked"
        assert ids == attachments and new == entry


DOCS = {
    "plan.md": {"hash": "b" * 64, "attachment_id": 5, "synced": "2026-10-02"},
    "spec.md": {"hash": "a" * 64, "attachment_id": 4, "synced": "2026-10-01"},
}
PATHS = {
    "spec.md": "/openproject/api/v3/attachments/4/content",
    "plan.md": "/openproject/api/v3/attachments/5/content",
}


def test_render_block_is_deterministic_and_ordered():
    first = render_block(DOCS, PATHS)
    assert first == render_block(dict(reversed(list(DOCS.items()))), PATHS)
    rows = [line for line in first.splitlines() if line.startswith("| [")]
    assert [re.match(r"\| \[(.*?)\]", r).group(1) for r in rows] == ["spec.md", "plan.md"]
    assert first.startswith(BEGIN) and first.endswith(END)
    assert "`aaaaaaaa`" in first and "2026-10-01" in first


def test_render_block_links_are_paths_without_host():
    block = render_block(DOCS, PATHS)
    assert "](/openproject/api/v3/attachments/4/content)" in block
    assert not re.search(r"https?://|attachment:", block)


def test_render_block_fallback_without_link_path():
    block = render_block(DOCS, {"spec.md": None, "plan.md": PATHS["plan.md"]})
    assert "| `spec.md` | `aaaaaaaa` | 2026-10-01 |" in block
    assert "[plan.md](" in block


def test_link_path_never_returns_a_host():
    assert link_path("http://host.example/openproject/api/v3/attachments/4/content") == (
        "/openproject/api/v3/attachments/4/content"
    )
    assert link_path("/openproject/api/v3/attachments/4/content") == (
        "/openproject/api/v3/attachments/4/content"
    )
    assert link_path("") is None and link_path(None) is None
    assert link_path("not a url") is None


def test_strip_wrapper_removes_exactly_the_outer_wrapper(root):
    data = json.loads((root / "tests/fixtures/docs/description-roundtrip.json").read_text())
    stripped = strip_wrapper(data["get_work_package_description"])
    assert stripped == data["written_raw"]
    assert strip_wrapper("plain") == "plain"
    assert strip_wrapper("<user-content>a <user-content>b</user-content></user-content>") == (
        "a <user-content>b</user-content>"
    )


def test_description_roundtrip_fixture_is_replaced_without_change(root):
    data = json.loads((root / "tests/fixtures/docs/description-roundtrip.json").read_text())
    raw = strip_wrapper(data["get_work_package_description"])
    block = raw[raw.index(BEGIN) : raw.index(END) + len(END)]
    assert replace_block(raw, block) == raw
    assert not description_needs_write(raw, block)


def test_replace_block_keeps_text_outside_byte_for_byte(root):
    text = fixture_text(root, "summary-text-around.md")
    new_block = render_block(DOCS, PATHS)
    out = replace_block(text, new_block)
    before = text[: text.index(BEGIN)]
    after = text[text.index(END) + len(END) :]
    assert out == before + new_block + after
    assert out.startswith("Intro written by a user.\n\n")
    assert out.endswith("\n\nNotes written by another user.")


def test_replace_block_appends_once_and_is_stable(root):
    text = fixture_text(root, "summary-no-block.md")
    block = render_block(DOCS, PATHS)
    out = replace_block(text, block)
    assert out == "Plain description without markers.\n\n" + block
    assert replace_block(out, block) == out
    assert replace_block("", block) == block


def test_replace_block_refuses_inconsistent_markers(root):
    block = render_block(DOCS, PATHS)
    for name in ("summary-dup-markers.md", "summary-end-before-begin.md", "summary-missing-end.md"):
        with pytest.raises(BlockError):
            replace_block(fixture_text(root, name), block)


def test_unchanged_documents_cause_no_description_write(root):
    block = render_block(DOCS, PATHS)
    description = "text\n\n" + block + "\n\nmore"
    assert not description_needs_write(description, block)
    changed = render_block({**DOCS, "spec.md": {**DOCS["spec.md"], "hash": "c" * 64}}, PATHS)
    assert description_needs_write(description, changed)
