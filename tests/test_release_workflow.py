"""Structural checks for .github/workflows/release.yml (contracts/release-workflow.md)."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"


def _load() -> tuple[dict, str]:
    text = WORKFLOW.read_text()
    # PyYAML parses the bare key `on` as boolean True.
    return yaml.safe_load(text), text


def _runs(job: dict) -> str:
    return "\n".join(step.get("run", "") for step in job["steps"])


def test_triggers_only_release_tags():
    data, _ = _load()
    assert data[True] == {"push": {"tags": ["preset-v*", "extension-v*", "bundle-v*"]}}


def test_job_permissions_and_order():
    data, _ = _load()
    verify, publish = data["jobs"]["verify"], data["jobs"]["publish"]
    assert verify["permissions"] == {"contents": "read"}
    assert publish["permissions"] == {"contents": "write"}
    assert publish["needs"] == "verify"


def test_verify_gates_before_publishing():
    data, _ = _load()
    runs = _runs(data["jobs"]["verify"])
    for command in (
        "uv sync",
        "release.py check",
        "ruff check",
        "ruff format --check",
        "pytest",
        "release.py build",
        "release.py verify-archive",
        "release.py notes",
        "<!-- release-commit: %s -->",
    ):
        assert command in runs, command


def test_publish_never_overwrites_or_edits():
    data, _ = _load()
    runs = _runs(data["jobs"]["publish"])
    assert "uv " not in runs
    assert "python3 scripts/release.py publish-plan" in runs
    assert "gh release view" in runs
    assert "gh release create" in runs
    assert "gh release upload" in runs
    assert "--clobber" not in runs
    assert "gh release edit" not in runs
    assert "--prerelease --latest=false" in runs


def test_only_github_token_is_used():
    _, text = _load()
    assert set(re.findall(r"secrets\.(\w+)", text)) <= {"GITHUB_TOKEN"}
    assert "OPENPROJECT" not in text.upper().replace("NO OPENPROJECT", "")
    assert "mcp" not in text.lower().replace("no mcp", "")


def test_bundle_steps_resolve_components_and_build():
    data, _ = _load()
    steps = data["jobs"]["verify"]["steps"]
    bundle = [s for s in steps if s.get("if") == "steps.meta.outputs.kind == 'bundle'"]
    assert len(bundle) == 1
    run = bundle[0]["run"]
    for command in (
        "release.component_tags",
        "gh release view",
        "missing release: $tag",
        "gh release download",
        "release.py bundle-catalog",
        "specify bundle validate --offline --path bundle",
        "specify bundle build --path bundle --output dist",
        'release.py verify-archive "dist/$ARCHIVE"',
    ):
        assert command in run, command
    assert "--download-base" not in run
    assert "not supported" not in run
