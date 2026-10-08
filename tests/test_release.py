"""Tests for scripts/release.py (feature 006, contracts/release-script.md)."""

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import zipfile

import pytest
import yaml
from conftest import ROOT

FIXTURES = ROOT / "tests/fixtures/release"
REPO = "Nachklang-io/speckit-openproject"

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
        ("bundle-v0.1.0", "bundle", "0.1.0", "", "openproject-0.1.0.zip"),
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


# --- check / notes (T007, T008) ---


def make_tree(tmp_path, override: str | None = None, changelog: str = "changelog-valid.md"):
    """Copy the real manifests into tmp_path, apply an override fixture, add a changelog."""
    for kind in ("preset", "extension"):
        (tmp_path / kind).mkdir()
        shutil.copy(ROOT / kind / f"{kind}.yml", tmp_path / kind / f"{kind}.yml")
    if override:
        patch = yaml.safe_load(fixture_text(f"manifests/{override}"))
        for kind, fields in patch.items():
            path = tmp_path / kind / f"{kind}.yml"
            data = yaml.safe_load(path.read_text())
            slug = fields.pop("repository_slug", None)
            if slug:
                fields["repository"] = f"https://github.com/{slug}"
            data[kind].update(fields)
            path.write_text(yaml.safe_dump(data, sort_keys=False))
    shutil.copy(FIXTURES / changelog, tmp_path / "CHANGELOG.md")
    return tmp_path


def set_version(tree, kind: str, version: str) -> None:
    path = tree / kind / f"{kind}.yml"
    data = yaml.safe_load(path.read_text())
    data[kind]["version"] = version
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def test_check_match(tmp_path):
    tree = make_tree(tmp_path)
    set_version(tree, "preset", "1.0.0")
    result = release.check(tree, "preset-v1.0.0", REPO)
    assert result == {
        "kind": "preset",
        "version": "1.0.0",
        "tag": "preset-v1.0.0",
        "prerelease": False,
        "archive": "openproject-preset-1.0.0.zip",
    }


def test_check_prerelease_compares_core_only(tmp_path):
    tree = make_tree(tmp_path)
    set_version(tree, "extension", "0.1.0")
    result = release.check(tree, "extension-v0.1.0-rc.1")
    assert result["version"] == "0.1.0"
    assert result["prerelease"] is True
    assert result["archive"] == "openproject-extension-0.1.0-rc.1.zip"


def test_check_version_mismatch(tmp_path):
    tree = make_tree(tmp_path, "extension-version-mismatch.yml")
    with pytest.raises(
        release.ReleaseError,
        match=r"^version mismatch: tag 0\.1\.0 vs extension/extension\.yml 0\.1\.1$",
    ):
        release.check(tree, "extension-v0.1.0")


def test_check_missing_changelog(tmp_path):
    tree = make_tree(tmp_path, changelog="changelog-missing-entry.md")
    set_version(tree, "extension", "0.1.0")
    with pytest.raises(release.ReleaseError, match="missing changelog entry: Extension 0.1.0"):
        release.check(tree, "extension-v0.1.0")


def test_check_repository_mismatch(tmp_path):
    tree = make_tree(tmp_path, "extension-repo-mismatch.yml")
    with pytest.raises(release.ReleaseError, match=r"^repository mismatch: manifest https://"):
        release.check(tree, "extension-v0.1.0", REPO)
    # Without --repository the gate does not apply.
    assert release.check(tree, "extension-v0.1.0")["kind"] == "extension"


def test_shipped_manifests_point_to_publishing_repo():
    for kind in ("preset", "extension"):
        data = release.load_manifest(ROOT, kind)
        assert data[kind]["repository"] == f"https://github.com/{REPO}"


def test_notes_cli(capsys, monkeypatch, tmp_path):
    monkeypatch.setattr(release, "ROOT", make_tree(tmp_path))
    assert release.main(["notes", "bundle", "0.1.0"]) == 0
    assert capsys.readouterr().out == "#### Added\n- First bundle.\n"
    assert release.main(["notes", "preset", "9.9.9"]) == 1
    assert "release: missing changelog entry: Preset 9.9.9" in capsys.readouterr().err


def test_check_cli_prints_json(capsys, monkeypatch, tmp_path):
    tree = make_tree(tmp_path)
    set_version(tree, "preset", "1.0.0")
    monkeypatch.setattr(release, "ROOT", tree)
    assert release.main(["check", "preset-v1.0.0"]) == 0
    assert json.loads(capsys.readouterr().out)["tag"] == "preset-v1.0.0"


def test_usage_error_exits_2():
    with pytest.raises(SystemExit) as exc:
        release.main(["notes", "docs", "1.0.0"])
    assert exc.value.code == 2


# --- build (T009) ---

EXPECTED_ENTRIES = {
    "preset": [
        "LICENSE",
        "README.md",
        "commands/speckit.taskstoissues.md",
        "openproject-config.template.yml",
        "preset.yml",
    ],
    "extension": [
        "LICENSE",
        "README.md",
        "commands/discover-fields.md",
        "commands/log-time.md",
        "commands/sync-docs.md",
        "commands/sync-status.md",
        "commands/sync-version.md",
        "extension.yml",
    ],
}


@pytest.mark.parametrize("kind", ["preset", "extension"])
def test_build_exact_entries_and_reproducible(kind, tmp_path):
    first, digest1 = release.build(ROOT, kind, tmp_path / "a", "1.2.3-rc.1")
    _, digest2 = release.build(ROOT, kind, tmp_path / "b", "1.2.3-rc.1")
    assert first.name == f"openproject-{kind}-1.2.3-rc.1.zip"
    assert digest1 == digest2 == hashlib.sha256(first.read_bytes()).hexdigest()
    with zipfile.ZipFile(first) as archive:
        infos = archive.infolist()
    assert [i.filename for i in infos] == EXPECTED_ENTRIES[kind]
    for info in infos:
        assert info.date_time == (1980, 1, 1, 0, 0, 0)
        assert info.external_attr >> 16 == 0o100644
        assert info.compress_type == zipfile.ZIP_DEFLATED


def test_build_excludes_hidden_and_bytecode(tmp_path):
    pkg = tmp_path / "src" / "extension"
    (pkg / "commands" / "__pycache__").mkdir(parents=True)
    (pkg / "extension.yml").write_text("extension: {version: 0.1.0}\n")
    (pkg / "commands" / "a.md").write_text("a\n")
    (pkg / "commands" / "__pycache__" / "x.pyc").write_bytes(b"\0")
    (pkg / "stray.pyc").write_bytes(b"\0")
    (pkg / ".DS_Store").write_bytes(b"\0")
    (pkg / ".hidden").mkdir()
    (pkg / ".hidden" / "f.md").write_text("f\n")
    target, _ = release.build(tmp_path / "src", "extension", tmp_path / "out")
    with zipfile.ZipFile(target) as archive:
        assert archive.namelist() == ["commands/a.md", "extension.yml"]
    assert target.name == "openproject-extension-0.1.0.zip"


# --- verify-archive (T010) ---


def write_zip(path, entries: dict[str, str]):
    with zipfile.ZipFile(path, "w") as archive:
        for name, text in entries.items():
            archive.writestr(name, text)
    return path


@pytest.mark.parametrize("kind", ["preset", "extension"])
def test_verify_built_archive_passes(kind, tmp_path):
    target, _ = release.build(ROOT, kind, tmp_path)
    assert release.archive_violations(target) == []


def _token() -> str:
    # Built at runtime so no token-shaped string lives in a fixture or source line.
    return "OPENPROJECT_API_TOKEN" + "=" + "a1B2" * 5


def _url(host: str) -> str:
    return "https" + "://" + host + "/path"


@pytest.mark.parametrize(
    ("entries", "expected"),
    [
        ({"README.md": "x"}, "manifest missing at archive root"),
        ({"preset.yml": "x", ".env": "x"}, "forbidden path: .env"),
        ({"preset.yml": "x", "commands/.env": "x"}, "forbidden path: commands/.env"),
        ({"preset.yml": "x", "tests/t.py": "x"}, "forbidden path: tests/t.py"),
        ({"preset.yml": "x", "docs/a.md": "x"}, "forbidden path: docs/a.md"),
        ({"preset.yml": "x", "specs/a/spec.md": "x"}, "forbidden path: specs/a/spec.md"),
        ({"preset.yml": "x", ".scratch/a": "x"}, "forbidden path: .scratch/a"),
        ({"preset.yml": "x", "../evil.md": "x"}, "unsafe path: ../evil.md"),
        ({"preset.yml": "x", "/abs.md": "x"}, "unsafe path: /abs.md"),
        ({"preset.yml": "TOKEN"}, "token-like string in preset.yml"),
        ({"bundle.yml": "x", "README.md": "TOKEN"}, "token-like string in README.md"),
        ({"preset.yml": "URL"}, "host not allowed in preset.yml: op.internal.test"),
    ],
)
def test_verify_violations(entries, expected, tmp_path):
    entries = {
        name: text.replace("TOKEN", _token()).replace("URL", _url("op.internal.test"))
        for name, text in entries.items()
    }
    violations = release.archive_violations(write_zip(tmp_path / "a.zip", entries))
    assert expected in violations


def test_verify_allowed_hosts_and_subdomains(tmp_path):
    text = " ".join(
        _url(h)
        for h in ("github.com", "raw.githubusercontent.com", "www.openproject.org", "x.example.com")
    )
    zip_path = write_zip(tmp_path / "a.zip", {"extension.yml": text})
    assert release.archive_violations(zip_path) == []
    zip_path = write_zip(tmp_path / "b.zip", {"extension.yml": _url("notgithub.com")})
    assert release.archive_violations(zip_path) == [
        "host not allowed in extension.yml: notgithub.com"
    ]


@pytest.mark.parametrize(
    "text",
    [
        '"OPENPROJECT_API_TOKEN": "' + "a1B2" * 5 + '"',
        "OPENPROJECT_API_KEY: " + "a1B2" * 5,
    ],
)
def test_verify_token_json_and_key_forms(text, tmp_path):
    zip_path = write_zip(tmp_path / "a.zip", {"extension.yml": text})
    assert release.archive_violations(zip_path) == ["token-like string in extension.yml"]


def test_verify_bundle_archive_passes(tmp_path):
    zip_path = write_zip(
        tmp_path / "a.zip",
        {"bundle.yml": BUNDLE.read_text(), "README.md": (ROOT / "bundle/README.md").read_text()},
    )
    assert release.archive_violations(zip_path) == []


@pytest.mark.parametrize(
    "name", ["script.sh", "lib/helper.py", "commands/nested/a.md", "commands/a.sh", "config.json"]
)
def test_verify_rejects_unexpected_entries(name, tmp_path):
    zip_path = write_zip(tmp_path / "a.zip", {"preset.yml": "x", name: "x"})
    assert release.archive_violations(zip_path) == [f"entry not allowed: {name}"]


def test_verify_text_cli(capsys, tmp_path):
    clean = tmp_path / "notes.md"
    clean.write_text("See " + _url("github.com") + "\n")
    dirty = tmp_path / "catalog.json"
    dirty.write_text(json.dumps({"url": _url("op.internal.test"), "x": _token()}))
    assert release.main(["verify-text", str(clean)]) == 0
    assert release.main(["verify-text", str(clean), str(dirty)]) == 1
    err = capsys.readouterr().err.splitlines()
    assert f"release: token-like string in {dirty}" in err
    assert f"release: host not allowed in {dirty}: op.internal.test" in err


def test_verify_cli_reports_all_violations(capsys, tmp_path):
    zip_path = write_zip(tmp_path / "a.zip", {".env": "x", "tests/t.py": _token()})
    assert release.main(["verify-archive", str(zip_path)]) == 1
    err = capsys.readouterr().err.splitlines()
    assert "release: manifest missing at archive root" in err
    assert "release: forbidden path: .env" in err
    assert "release: forbidden path: tests/t.py" in err
    assert "release: token-like string in tests/t.py" in err


# --- publish-plan (T012) ---


@pytest.mark.parametrize(
    ("marker", "present", "expected"),
    [
        (None, [], {"action": "create", "upload": ["a.zip", "b.json"]}),
        ("abc", ["a.zip"], {"action": "upload", "upload": ["b.json"]}),
        ("abc", ["a.zip", "b.json"], {"action": "noop", "upload": []}),
    ],
)
def test_publish_plan_states(marker, present, expected):
    assert release.publish_plan("preset-v1.0.0", "abc", marker, ["a.zip", "b.json"], present) == (
        expected
    )


@pytest.mark.parametrize(
    ("marker", "present", "shown"),
    [
        ("def", ["a.zip"], "def"),
        ("", ["a.zip"], "unknown"),
        ("", [], "unknown"),
        ("def", [], "def"),
    ],
)
def test_publish_plan_conflict(marker, present, shown):
    with pytest.raises(
        release.ReleaseError,
        match=rf"^conflict: release preset-v1\.0\.0 was created from {shown}, "
        r"tag now points to abc$",
    ):
        release.publish_plan("preset-v1.0.0", "abc", marker, ["a.zip"], present)


def test_publish_plan_runs_without_pyyaml(tmp_path):
    # The publish job runs it with a bare python3 (no uv sync): yaml must not be imported.
    script = ROOT / "scripts/release.py"
    blocker = tmp_path / "yaml.py"
    blocker.write_text("raise ImportError('yaml blocked')\n")
    env = {"PYTHONPATH": str(tmp_path), "PATH": "/usr/bin:/bin"}
    proc = subprocess.run(
        [sys.executable, str(script), "publish-plan", "--tag", "preset-v1.0.0", "--sha", "abc"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {"action": "create", "upload": []}


# --- the repository's own CHANGELOG.md (T020, SC-005) ---

GROUPS = {"Added", "Changed", "Fixed", "Removed", "Security", "Migration"}


def test_changelog_sections_and_headings():
    lines = (ROOT / "CHANGELOG.md").read_text().splitlines()
    sections = [line[3:].strip() for line in lines if line.startswith("## ")]
    assert sections == ["Preset", "Extension", "Bundle"]
    current = None
    first_sub: dict[str, str] = {}
    for line in lines:
        if line.startswith("## "):
            current = line[3:].strip()
        elif line.startswith("### "):
            first_sub.setdefault(current, line)
            assert line == "### Unreleased" or release.VERSION_HEADING_RE.match(line), line
            assert "-rc" not in line, line
        elif line.startswith("#### "):
            assert line[5:].strip() in GROUPS, line
    assert all(first_sub[s] == "### Unreleased" for s in sections), first_sub


@pytest.mark.parametrize("kind", ["preset", "extension", "bundle"])
def test_changelog_has_entry_for_manifest_version(kind):
    path = ROOT / release.manifest_path(kind)
    if not path.exists():
        pytest.skip(f"{path.name} not created yet")
    version = str(release.load_manifest(ROOT, kind)[kind]["version"])
    entry = release.changelog_entry((ROOT / "CHANGELOG.md").read_text(), kind, version)
    assert entry.strip()


# --- bundle catalogs (T024) ---

BUNDLE = ROOT / "bundle/bundle.yml"


def bundle_pin_map() -> dict[str, str]:
    return release.bundle_pins(yaml.safe_load(BUNDLE.read_text()))


@pytest.mark.parametrize(
    "tag, expected",
    [
        ("bundle-v0.1.0", {"preset": "preset-v{p}", "extension": "extension-v{e}"}),
        (
            "bundle-v0.1.0-rc.1",
            {"preset": "preset-v{p}-rc.1", "extension": "extension-v{e}-rc.1"},
        ),
    ],
)
def test_component_tags(tag, expected):
    pins = {"preset": "1.0.0", "extension": "0.1.0"}
    tags = release.component_tags(release.parse_tag(tag), pins)
    names = {kind: t.name for kind, t in tags.items()}
    assert names == {k: v.format(p="1.0.0", e="0.1.0") for k, v in expected.items()}


def test_check_bundle_on_repo():
    version = str(release.load_manifest(ROOT, "bundle")["bundle"]["version"])
    assert release.check(ROOT, f"bundle-v{version}")["kind"] == "bundle"


def test_check_bundle_speckit_range_mismatch(tmp_path):
    for kind in ("preset", "extension", "bundle"):
        (tmp_path / kind).mkdir()
        shutil.copy(ROOT / release.manifest_path(kind), tmp_path / release.manifest_path(kind))
    shutil.copy(ROOT / "CHANGELOG.md", tmp_path / "CHANGELOG.md")
    path = tmp_path / "bundle/bundle.yml"
    data = yaml.safe_load(path.read_text())
    data["requires"]["speckit_version"] = ">=1.2.0"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    version = data["bundle"]["version"]
    with pytest.raises(
        release.ReleaseError,
        match=r"^speckit_version mismatch: bundle >=1\.2\.0 vs preset >=1\.1\.0$",
    ):
        release.check(tmp_path, f"bundle-v{version}")


def test_bundle_pins_read_provides():
    assert release.bundle_pins(yaml.safe_load(BUNDLE.read_text())) == {
        "preset": "1.0.0",
        "extension": "0.1.0",
    }


@pytest.mark.parametrize(
    "provides",
    [{}, {"presets": [{"id": "openproject", "version": "1.0.0"}]}],
)
def test_bundle_pins_need_one_entry_each(provides):
    with pytest.raises(release.ReleaseError, match="exactly one openproject"):
        release.bundle_pins({"provides": provides})


def build_components(tmp_path, suffix: str = ""):
    archives = tmp_path / "archives"
    for kind, pin in bundle_pin_map().items():
        release.build(ROOT, kind, archives, f"{pin}{suffix}")
    return archives


def run_bundle_catalog(tmp_path, tag="bundle-v0.1.0", archives=None, base=None):
    archives = archives or build_components(tmp_path)
    return release.bundle_catalog(
        ROOT, BUNDLE, tag, archives, REPO, tmp_path / "out", base, "2026-10-08T00:00:00Z"
    )


@pytest.mark.parametrize("suffix", ["", "-rc.1"])
def test_bundle_catalog_shape(tmp_path, suffix):
    archives = build_components(tmp_path, suffix)
    written = run_bundle_catalog(tmp_path, f"bundle-v0.1.0{suffix}", archives)
    assert [p.name for p in written] == [
        "openproject-presets-catalog.json",
        "openproject-extensions-catalog.json",
    ]
    pins = bundle_pin_map()
    for path, (kind, key) in zip(written, (("preset", "presets"), ("extension", "extensions"))):
        catalog = json.loads(path.read_text())
        assert set(catalog) == {"schema_version", "updated_at", key}
        assert catalog["schema_version"] == "1.0"
        entry = catalog[key]["openproject"]
        manifest = release.load_manifest(ROOT, kind)
        archive = f"openproject-{kind}-{pins[kind]}{suffix}.zip"
        assert entry == {
            "id": "openproject",
            "name": manifest[kind]["name"],
            "version": pins[kind],
            "description": manifest[kind]["description"],
            "author": manifest[kind]["author"],
            "license": manifest[kind]["license"],
            "repository": f"https://github.com/{REPO}",
            "download_url": (
                f"https://github.com/{REPO}/releases/download/{kind}-v{pins[kind]}{suffix}/{archive}"
            ),
            "sha256": hashlib.sha256((archives / archive).read_bytes()).hexdigest(),
            "requires": {"speckit_version": manifest["requires"]["speckit_version"]},
        }


def test_bundle_catalog_is_deterministic_except_updated_at(tmp_path):
    first = [p.read_text() for p in run_bundle_catalog(tmp_path)]
    second = [p.read_text() for p in run_bundle_catalog(tmp_path)]
    assert first == second


def test_bundle_catalog_download_base(tmp_path):
    written = run_bundle_catalog(tmp_path, base="http://127.0.0.1:8123/")
    entry = json.loads(written[0].read_text())["presets"]["openproject"]
    assert entry["download_url"] == "http://127.0.0.1:8123/openproject-preset-1.0.0.zip"


def test_bundle_catalog_missing_archive(tmp_path):
    archives = build_components(tmp_path)
    (archives / "openproject-extension-0.1.0.zip").unlink()
    with pytest.raises(release.ReleaseError, match=r"missing release archive: openproject-ext"):
        run_bundle_catalog(tmp_path, archives=archives)


def test_bundle_catalog_rc_needs_rc_archives(tmp_path):
    with pytest.raises(release.ReleaseError, match=r"missing release archive: .*-1\.0\.0-rc\.1"):
        run_bundle_catalog(tmp_path, tag="bundle-v0.1.0-rc.1")


def test_bundle_catalog_pin_mismatch(tmp_path):
    archives = build_components(tmp_path)
    write_zip(
        archives / "openproject-preset-1.0.0.zip", {"preset.yml": "preset:\n  version: 9.9.9\n"}
    )
    with pytest.raises(release.ReleaseError, match="pin mismatch"):
        run_bundle_catalog(tmp_path, archives=archives)


def test_bundle_catalog_rejects_component_tag(tmp_path):
    with pytest.raises(release.ReleaseError, match="not a bundle tag"):
        run_bundle_catalog(tmp_path, tag="preset-v1.0.0")


# --- catalog-submission checklists (T031, SC-006) ---

CATALOG = ROOT / "docs/catalog"
CHECKLISTS = ["preset-checklist.md", "extension-checklist.md", "bundle-checklist.md"]


def checklist_items(name: str) -> list[list[str]]:
    rows = []
    for line in (CATALOG / name).read_text().splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells[0].isdigit():
            rows.append(cells)
    return rows


@pytest.mark.parametrize("name", CHECKLISTS)
def test_checklist_items_have_state(name):
    items = checklist_items(name)
    assert items, f"{name} has no items"
    assert [int(item[0]) for item in items] == list(range(1, len(items) + 1))
    for number, requirement, evidence, state, reason in items:
        assert requirement, f"{name} #{number}: no requirement"
        assert state in {"met", "gap", "n/a"}, f"{name} #{number}: state {state!r}"
        if state == "met":
            assert evidence, f"{name} #{number}: met without evidence"
        else:
            assert reason, f"{name} #{number}: {state} without reason"
        if state == "gap":
            assert "Options:" in reason, f"{name} #{number}: gap without options"


@pytest.mark.parametrize(
    ("kind", "manifest", "tag"),
    [
        ("preset", "preset/preset.yml", "preset-v{v}"),
        ("extension", "extension/extension.yml", "extension-v{v}"),
    ],
)
def test_catalog_entry_matches_manifest(kind, manifest, tag):
    data = yaml.safe_load((ROOT / manifest).read_text())
    meta = data[kind]
    entry = json.loads((CATALOG / f"{kind}-entry.json").read_text())[meta["id"]]
    for key in ("id", "name", "version", "description", "author", "repository", "license"):
        assert entry[key] == meta[key], key
    assert entry["requires"]["speckit_version"] == data["requires"]["speckit_version"]
    assert entry["tags"] == data["tags"]
    version = meta["version"]
    archive = f"openproject-{kind}-{version}.zip"
    assert entry["download_url"] == (
        f"https://github.com/{REPO}/releases/download/{tag.format(v=version)}/{archive}"
    )
    assert f"/blob/{tag.format(v=version)}/{kind}/README.md" in entry["documentation"]
