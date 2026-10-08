"""Install smoke test for release archives (quickstart Q2).

Builds both archives, serves them on 127.0.0.1 and installs them with ``--from`` into a fresh
spec-kit project. Needs the `specify` CLI; skipped otherwise unless SPECKIT_REQUIRE_CLI=1, which
CI sets so a missing CLI fails instead of passing silently.
"""

import functools
import http.server
import importlib.util
import os
import shutil
import subprocess
import sys
import threading

import pytest
from conftest import ROOT

_spec = importlib.util.spec_from_file_location("release", ROOT / "scripts/release.py")
release = sys.modules.get("release") or importlib.util.module_from_spec(_spec)
if "release" not in sys.modules:
    sys.modules["release"] = release
    _spec.loader.exec_module(release)

if os.environ.get("SPECKIT_REQUIRE_CLI") != "1":
    pytestmark = pytest.mark.skipif(
        shutil.which("specify") is None, reason="specify CLI not installed"
    )

PRESET_VERSION = "1.0.0"
EXTENSION_VERSION = "0.1.0"


def run(cmd, cwd, answer=None):
    result = subprocess.run(cmd, cwd=cwd, input=answer, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        pytest.fail(
            f"{' '.join(cmd)} exited with {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    return result


@pytest.fixture()
def served(root, tmp_path):
    dist = tmp_path / "dist"
    names = {}
    for kind, version in (("preset", PRESET_VERSION), ("extension", EXTENSION_VERSION)):
        target, _ = release.build(root, kind, dist, f"{version}-rc.1")
        assert release.archive_violations(target) == []
        names[kind] = target.name
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(dist))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        yield {kind: f"{base}/{name}" for kind, name in names.items()}
    finally:
        server.shutdown()
        server.server_close()


def test_archives_install_from_url(served, tmp_path):
    run(
        [
            "specify",
            "init",
            "proj",
            "--non-interactive",
            "--integration",
            "claude",
            "--ignore-agent-tools",
        ],
        tmp_path,
    )
    project = tmp_path / "proj"
    run(["specify", "preset", "add", "--from", served["preset"]], project)
    # `extension add --from` asks to confirm the untrusted source.
    run(
        ["specify", "extension", "add", "openproject", "--from", served["extension"]],
        project,
        answer="y\n",
    )

    presets = run(["specify", "preset", "list"], project).stdout
    extensions = run(["specify", "extension", "list"], project).stdout
    # Lists show the manifest (core) version, not the rc suffix of the archive name.
    assert "(openproject)" in presets and f"v{PRESET_VERSION}" in presets, presets
    assert "openproject" in extensions and f"v{EXTENSION_VERSION}" in extensions, extensions

    skill = (project / ".claude/skills/speckit-taskstoissues/SKILL.md").read_text()
    assert "preset:openproject" in skill
    assert (project / ".claude/skills/speckit-openproject-discover-fields").is_dir()
