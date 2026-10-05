import re

import yaml

ID_RE = re.compile(r"^[a-z0-9-]+$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def load(path):
    return yaml.safe_load(path.read_text())


def test_preset_manifest(root):
    m = load(root / "preset" / "preset.yml")
    assert m["schema_version"] == "1.0"
    assert ID_RE.match(m["preset"]["id"])
    assert SEMVER_RE.match(m["preset"]["version"])
    assert "speckit_version" in m["requires"]
    for t in m["provides"]["templates"]:
        assert (root / "preset" / t["file"]).is_file()


def test_extension_manifest(root):
    m = load(root / "extension" / "extension.yml")
    assert m["schema_version"] == "1.0"
    assert ID_RE.match(m["extension"]["id"])
    assert SEMVER_RE.match(m["extension"]["version"])
    for c in m["provides"]["commands"]:
        assert c["name"].startswith(f"speckit.{m['extension']['id']}.")
        assert (root / "extension" / c["file"]).is_file()


def test_command_prompt_has_no_secrets(root):
    for p in (root / "preset").rglob("*.md"):
        assert "OPENPROJECT_API_TOKEN=" not in p.read_text()
