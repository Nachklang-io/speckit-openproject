"""The recorded server responses contain the fields the discover-fields prompt relies on."""

import json

import pytest

DIR = "tests/fixtures/discovery"


def load(root, name):
    return json.loads((root / DIR / name).read_text())


def blockers(context):
    return [
        f["key"]
        for f in context["custom_fields"]
        if f["required"] and f["writable"] and not f["has_default"]
    ]


def test_discovery_fixture_files_exist(root):
    for name in (
        "statuses.json",
        "context-task-plain.json",
        "context-task-mandatory.json",
        "README.md",
    ):
        assert (root / DIR / name).is_file(), name


def test_statuses_have_default_and_closed_flags(root):
    results = load(root, "statuses.json")["results"]
    assert results
    for status in results:
        assert {"id", "name", "is_default", "is_closed"} <= set(status)
    assert sum(s["is_default"] for s in results) == 1
    closed = {s["name"] for s in results if s["is_closed"]}
    assert {"Closed", "Rejected"} <= closed


@pytest.mark.parametrize("name", ["context-task-plain.json", "context-task-mandatory.json"])
def test_write_context_has_discovery_keys(root, name):
    ctx = load(root, name)
    for key in (
        "available_types",
        "available_statuses",
        "available_priorities",
        "available_versions",
        "fields",
        "custom_fields",
    ):
        assert key in ctx, key
    for field in ctx["custom_fields"]:
        assert {
            "key",
            "name",
            "type",
            "required",
            "writable",
            "has_default",
            "allowed_values",
        } <= set(field)
        assert field["key"].startswith("customField")


def test_available_statuses_are_known_statuses(root):
    names = {s["name"] for s in load(root, "statuses.json")["results"]}
    for s in load(root, "context-task-plain.json")["available_statuses"]:
        assert s["title"] in names


def test_blocker_rule_distinguishes_plain_and_mandatory(root):
    assert blockers(load(root, "context-task-plain.json")) == []
    assert blockers(load(root, "context-task-mandatory.json")) == ["customField1"]


def test_derived_fixture_differs_only_in_required_flag(root):
    plain = load(root, "context-task-plain.json")
    mand = load(root, "context-task-mandatory.json")
    for ctx in (plain, mand):
        for f in ctx["fields"] + ctx["custom_fields"]:
            if f["key"] == "customField1":
                f["required"] = None
    assert plain == mand


def test_fixtures_contain_no_hosts_or_secrets(root):
    for path in (root / DIR).glob("*.json"):
        text = path.read_text().lower()
        assert "http://" not in text and "https://" not in text
        assert "token" not in text and "apikey" not in text
