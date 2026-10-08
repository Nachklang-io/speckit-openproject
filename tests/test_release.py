"""Tests for scripts/release.py (feature 006, contracts/release-script.md)."""

import importlib.util
import sys

import pytest
from conftest import ROOT

FIXTURES = ROOT / "tests/fixtures/release"

_spec = importlib.util.spec_from_file_location("release", ROOT / "scripts/release.py")
release = importlib.util.module_from_spec(_spec)
sys.modules["release"] = release
_spec.loader.exec_module(release)


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text()


# --- tag grammar (T004) ---


@pytest.mark.parametrize(
    ("name", "kind", "core", "suffix", "archive"),
    [
        ("preset-v1.0.0", "preset", "1.0.0", "", "openproject-preset-1.0.0.zip"),
        ("extension-v0.1.0", "extension", "0.1.0", "", "openproject-extension-0.1.0.zip"),
        ("bundle-v0.1.0", "bundle", "0.1.0", "", "openproject-bundle-0.1.0.zip"),
        (
            "extension-v0.1.0-rc.1",
            "extension",
            "0.1.0",
            "rc.1",
            "openproject-extension-0.1.0-rc.1.zip",
        ),
        (
            "preset-v10.20.30-beta",
            "preset",
            "10.20.30",
            "beta",
            "openproject-preset-10.20.30-beta.zip",
        ),
    ],
)
def test_parse_valid_tag(name, kind, core, suffix, archive):
    tag = release.parse_tag(name)
    assert (tag.kind, tag.core, tag.suffix, tag.archive) == (kind, core, suffix, archive)
    assert tag.prerelease is bool(suffix)


@pytest.mark.parametrize(
    "name",
    [
        "v1.0.0",
        "extension-v1.0",
        "preset-v01.0.0",
        "preset-v1.00.0",
        "preset-1.0.0",
        "docs-v1.0.0",
        "preset-v1.0.0-",
        "preset-v1.0.0-rc..1",
        "preset-v1.0.0+build",
        " preset-v1.0.0",
    ],
)
def test_parse_invalid_tag(name):
    with pytest.raises(release.ReleaseError, match=r"^not a release tag: "):
        release.parse_tag(name)


# --- changelog parser (T005) ---


def test_entry_found_verbatim():
    body = release.changelog_entry(fixture_text("changelog-valid.md"), "preset", "1.0.0")
    assert body == "#### Added\n- First release.\n"


def test_entry_stops_at_next_heading():
    text = fixture_text("changelog-valid.md")
    assert release.changelog_entry(text, "preset", "0.9.0") == "#### Fixed\n- Older entry.\n"
    assert release.changelog_entry(text, "bundle", "0.1.0") == "#### Added\n- First bundle.\n"


def test_entry_is_scoped_to_section():
    # Extension and Bundle both have 0.1.0; the bundle body must not leak into the extension.
    body = release.changelog_entry(fixture_text("changelog-valid.md"), "extension", "0.1.0")
    assert "First bundle" not in body
    assert "#### Migration\n- Use the new command name." in body


def test_unreleased_is_never_an_entry():
    with pytest.raises(release.ReleaseError, match="missing changelog entry: Preset 1.1.0"):
        release.changelog_entry(fixture_text("changelog-valid.md"), "preset", "1.1.0")


def test_missing_entry():
    with pytest.raises(release.ReleaseError, match=r"^missing changelog entry: Extension 0\.1\.0$"):
        release.changelog_entry(fixture_text("changelog-missing-entry.md"), "extension", "0.1.0")


def test_empty_entry():
    with pytest.raises(release.ReleaseError, match=r"^missing changelog entry: Preset 1\.0\.0$"):
        release.changelog_entry(fixture_text("changelog-empty-entry.md"), "preset", "1.0.0")


def test_breaking_without_migration():
    with pytest.raises(
        release.ReleaseError,
        match=r"^breaking change without migration note: Extension 0\.1\.0$",
    ):
        release.changelog_entry(
            fixture_text("changelog-breaking-no-migration.md"), "extension", "0.1.0"
        )
