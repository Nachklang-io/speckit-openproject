"""Install smoke test: needs the `specify` CLI, skipped otherwise."""

import shutil
import subprocess

import pytest

pytestmark = pytest.mark.skipif(shutil.which("specify") is None, reason="specify CLI not installed")


def run(cmd, cwd):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        version = subprocess.run(
            ["specify", "--version"], capture_output=True, text=True, check=False
        )
        pytest.fail(
            f"{' '.join(cmd)} exited with {result.returncode} "
            f"(specify: {version.stdout.strip() or version.stderr.strip()})\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    return result


@pytest.fixture()
def project(tmp_path):
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
    return tmp_path / "proj"


def test_preset_overrides_taskstoissues(root, project):
    run(["specify", "preset", "add", "--dev", str(root / "preset")], project)
    skill = (project / ".claude/skills/speckit-taskstoissues/SKILL.md").read_text()
    assert "OpenProject" in skill
    assert "preset:openproject" in skill


def test_extension_installs(root, project):
    run(["specify", "extension", "add", "--dev", str(root / "extension")], project)
    assert (project / ".claude/skills/speckit-openproject-discover-fields").is_dir()
