import json
import re

from conftest import ROOT
from version_time_reference import (
    check_entry_key_ambiguity,
    classify_time,
    entry_key,
    parse_line,
    resolve_task_key,
    to_iso,
)

DURATIONS = json.loads((ROOT / "tests/fixtures/time/durations.json").read_text())
PLAN_KEY_PRESENT = json.loads((ROOT / "tests/fixtures/time/plan-key-present.json").read_text())
PLAN_ENTRY_KEY = json.loads((ROOT / "tests/fixtures/time/plan-entry-key.json").read_text())
PLAN_UNKNOWN_KEY = json.loads((ROOT / "tests/fixtures/time/plan-unknown-key.json").read_text())
PLAN_HASH_ID = json.loads((ROOT / "tests/fixtures/time/plan-hash-id.json").read_text())

# tests/fixtures/mapping.schema.json's `time_entries[].hours` pattern - kept in sync with the
# schema by tests/test_schemas.py; checked again here against every accepted duration.
HOURS_PATTERN = re.compile(r"^PT(\d+H)?(\d+M)?$")


def pytest_generate_tests(metafunc):
    if "duration_case" in metafunc.fixturenames:
        metafunc.parametrize(
            "duration_case", DURATIONS["cases"], ids=[c["name"] for c in DURATIONS["cases"]]
        )
    if "entry_key_case" in metafunc.fixturenames:
        metafunc.parametrize(
            "entry_key_case",
            PLAN_ENTRY_KEY["cases"],
            ids=[c["name"] for c in PLAN_ENTRY_KEY["cases"]],
        )
    if "hash_id_case" in metafunc.fixturenames:
        metafunc.parametrize(
            "hash_id_case", PLAN_HASH_ID["cases"], ids=[c["name"] for c in PLAN_HASH_ID["cases"]]
        )


def test_every_duration_case(duration_case):
    got = parse_line(duration_case["line"], DURATIONS["today"])
    if duration_case["expect"] == "rejected":
        assert isinstance(got, str), f"{duration_case['name']}: expected rejection, got {got}"
    else:
        assert isinstance(got, dict), f"{duration_case['name']}: expected a parse, got {got!r}"
        assert got["minutes"] == duration_case["expect"]["minutes"]
        assert got["date"] == duration_case["expect"]["date"]


def test_to_iso_matches_the_ledger_schema_pattern_for_every_accepted_duration(duration_case):
    if duration_case["expect"] == "rejected":
        return
    iso = to_iso(duration_case["expect"]["minutes"])
    assert HOURS_PATTERN.match(iso), f"{duration_case['name']}: {iso!r}"


def test_key_present_in_the_ledger_is_unchanged():
    item = PLAN_KEY_PRESENT["item"]
    key = entry_key(item["work_package_id"], item["spent_on"], item["activity"], item["iso"])
    got = classify_time({"key": key}, PLAN_KEY_PRESENT["ledger_time_entries"])
    assert got == PLAN_KEY_PRESENT["expect"]


def test_entry_key_ambiguity_and_override(entry_key_case):
    ambiguity = check_entry_key_ambiguity(
        entry_key_case["item_count"], entry_key_case["entry_key_given"]
    )
    assert ambiguity == entry_key_case["expect_ambiguity"]
    if ambiguity != "ok":
        return
    item = entry_key_case["item"]
    key = entry_key(
        item["work_package_id"],
        item["spent_on"],
        item["activity"],
        item["iso"],
        entry_key=entry_key_case["entry_key_value"],
    )
    assert key == entry_key_case["expect_key"]
    got = classify_time({"key": key}, entry_key_case["ledger_time_entries"])
    assert got == entry_key_case["expect_classify"]


def test_unknown_task_key():
    resolved = resolve_task_key(PLAN_UNKNOWN_KEY["key"], PLAN_UNKNOWN_KEY["ledger_items"])
    assert resolved == PLAN_UNKNOWN_KEY["expect_resolve"]
    got = classify_time({"key": "x", "known": resolved is not None}, [])
    assert got == PLAN_UNKNOWN_KEY["expect_classify"]


def test_hash_id_resolution(hash_id_case):
    resolved = resolve_task_key(hash_id_case["key"], PLAN_HASH_ID["ledger_items"])
    assert resolved == hash_id_case["expect_resolve"]
    if hash_id_case["expect_classify"] == "unknown":
        got = classify_time({"key": "x", "known": False}, [])
        assert got == "unknown"
    else:
        assert resolved is not None


def test_a_different_activity_gives_a_different_key():
    base = entry_key(111, "2026-10-07", "Development", "PT1H")
    other = entry_key(111, "2026-10-07", "Design", "PT1H")
    assert base != other


def test_a_different_date_gives_a_different_key():
    base = entry_key(111, "2026-10-07", "Development", "PT1H")
    other = entry_key(111, "2026-10-06", "Development", "PT1H")
    assert base != other


def test_entry_key_argument_replaces_the_computed_key():
    computed = entry_key(111, "2026-10-07", "Development", "PT1H")
    overridden = entry_key(111, "2026-10-07", "Development", "PT1H", entry_key="mine")
    assert overridden != computed
    assert overridden == "entry:mine"


def test_logging_the_same_line_twice_is_idempotent():
    """SC-002: once a created entry's key is in the ledger, classifying it again is unchanged."""
    key = entry_key(111, "2026-10-07", "Development", "PT1H30M")
    first = classify_time({"key": key}, [])
    assert first == "create"
    ledger_after = [{"key": key}]
    second = classify_time({"key": key}, ledger_after)
    assert second == "unchanged"
