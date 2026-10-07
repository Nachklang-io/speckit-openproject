import json

from conftest import ROOT
from version_time_reference import classify_version, classify_work_package

DATA = json.loads((ROOT / "tests/fixtures/version/decision-table.json").read_text())


def pytest_generate_tests(metafunc):
    if "version_case" in metafunc.fixturenames:
        metafunc.parametrize(
            "version_case",
            DATA["version_cases"],
            ids=[c["name"] for c in DATA["version_cases"]],
        )
    if "wp_case" in metafunc.fixturenames:
        metafunc.parametrize(
            "wp_case",
            DATA["work_package_cases"],
            ids=[c["name"] for c in DATA["work_package_cases"]],
        )


def test_every_version_row_of_the_table(version_case):
    got = classify_version(
        version_case["ledger_version"], version_case["matches"], version_case["status"]
    )
    for key, want in version_case["expect"].items():
        assert got.get(key) == want, f"{version_case['name']} / {key}: {got}"


def test_every_work_package_row_of_the_table(wp_case):
    got = classify_work_package(wp_case["wp_version"], wp_case["version_name"], wp_case["exists"])
    for key, want in wp_case["expect"].items():
        assert got.get(key) == want, f"{wp_case['name']} / {key}: {got}"


def test_version_reuse_is_idempotent_on_the_second_run(version_case):
    """SC-002: a second run against the state the first run left behind never writes again.

    Only "reuse" is checked here: "create" leaves with a version id only the actual
    create_version call would provide, not something this classifier can simulate.
    """
    first = classify_version(
        version_case["ledger_version"], version_case["matches"], version_case["status"]
    )
    if first["action"] != "reuse":
        return
    chosen = {"id": first["id"], "name": first["name"]}
    second = classify_version(chosen, [chosen], version_case["status"])
    assert second["action"] == "use"
    assert second["writes"] == []


def test_work_package_assign_is_idempotent_on_the_second_run(wp_case):
    """SC-002: applying an "assign" and classifying again yields "unchanged", never a duplicate."""
    first = classify_work_package(wp_case["wp_version"], wp_case["version_name"], wp_case["exists"])
    if first["action"] != "assign":
        return
    second = classify_work_package(wp_case["version_name"], wp_case["version_name"], True)
    assert second == {"action": "unchanged", "writes": []}


def test_other_and_stale_never_write_and_never_change_on_a_second_run(wp_case):
    """The work package is never moved onto a version it did not already carry."""
    first = classify_work_package(wp_case["wp_version"], wp_case["version_name"], wp_case["exists"])
    if first["action"] not in ("other", "stale"):
        return
    second = classify_work_package(
        wp_case["wp_version"], wp_case["version_name"], wp_case["exists"]
    )
    assert second == first
    assert second["writes"] == []
