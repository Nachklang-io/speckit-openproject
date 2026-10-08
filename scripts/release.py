#!/usr/bin/env python3
"""Release helper for the preset, extension and bundle packages (feature 006).

Contract: specs/006-release-engineering/contracts/release-script.md.

Exit codes: 0 ok, 1 a gate failed (message on stderr, prefixed ``release: ``), 2 usage error.
Uses the stdlib and PyYAML only. PyYAML is imported lazily so ``publish-plan`` runs on a bare
``python3``. No subcommand touches the network or writes outside ``--out``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

KINDS = ("preset", "extension", "bundle")
SECTIONS = {"preset": "Preset", "extension": "Extension", "bundle": "Bundle"}

TAG_RE = re.compile(
    r"^(preset|extension|bundle)-v"
    r"((?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))"
    r"(?:-([0-9A-Za-z]+(?:\.[0-9A-Za-z]+)*))?$"
)
VERSION_HEADING_RE = re.compile(r"^### (\d+\.\d+\.\d+) - \d{4}-\d{2}-\d{2}\s*$")
BREAKING_ITEM_RE = re.compile(r"^\s*[-*]\s+\*\*Breaking\*\*")
CORE_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")

ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)
FORBIDDEN_COMPONENTS = {".scratch", "tests", "specs", "docs"}
TOKEN_RE = re.compile(r"OPENPROJECT_API_TOKEN\s*[=:]\s*['\"]?[A-Za-z0-9_-]{16,}")
URL_HOST_RE = re.compile(r"https?://(?:[^/\s@\"'<>]*@)?([A-Za-z0-9.-]+)")
# Extending this allowlist is a reviewed code change (contracts/archive-layout.md).
ALLOWED_HOSTS = ("github.com", "raw.githubusercontent.com", "www.openproject.org", "example.com")


class ReleaseError(Exception):
    """A release gate failed. main() prints it with the ``release: `` prefix and exits 1."""


@dataclass(frozen=True)
class Tag:
    name: str
    kind: str
    core: str
    suffix: str  # pre-release suffix without the leading "-", or ""

    @property
    def prerelease(self) -> bool:
        return bool(self.suffix)

    @property
    def version(self) -> str:
        return f"{self.core}-{self.suffix}" if self.suffix else self.core

    @property
    def archive(self) -> str:
        return f"openproject-{self.kind}-{self.version}.zip"


def parse_tag(name: str) -> Tag:
    match = TAG_RE.match(name)
    if not match:
        raise ReleaseError(f"not a release tag: {name}")
    kind, core, suffix = match.groups()
    return Tag(name=name, kind=kind, core=core, suffix=suffix or "")


def changelog_entry(text: str, kind: str, core: str) -> str:
    """Return the body of the ``### <core> - <date>`` entry in the kind's section, verbatim."""
    section = SECTIONS[kind]
    in_section = False
    body: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            if body is not None:
                break
            in_section = line[3:].strip() == section
            continue
        if not in_section:
            continue
        if line.startswith("### "):
            if body is not None:
                break
            heading = VERSION_HEADING_RE.match(line)
            if heading and heading.group(1) == core:
                body = []
            continue
        if body is not None:
            body.append(line)

    entry = "\n".join(body or []).strip("\n")
    if not entry.strip():
        raise ReleaseError(f"missing changelog entry: {section} {core}")
    if _has_breaking_item(entry) and not _migration_text(entry):
        raise ReleaseError(f"breaking change without migration note: {section} {core}")
    return entry + "\n"


def _has_breaking_item(entry: str) -> bool:
    return any(BREAKING_ITEM_RE.match(line) for line in entry.splitlines())


def _migration_text(entry: str) -> str:
    group: str | None = None
    lines: list[str] = []
    for line in entry.splitlines():
        if line.startswith("#### "):
            group = line[5:].strip()
            continue
        if group == "Migration" and line.strip():
            lines.append(line)
    return "\n".join(lines)


def manifest_path(kind: str) -> str:
    return f"{kind}/{kind}.yml"


def load_manifest(root: Path, kind: str) -> dict:
    import yaml  # lazy: publish-plan must run without PyYAML

    path = root / manifest_path(kind)
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict) or not isinstance(data.get(kind), dict):
        raise ReleaseError(f"invalid manifest: {manifest_path(kind)}")
    return data


def check(root: Path, tag_name: str, repository: str | None = None) -> dict:
    tag = parse_tag(tag_name)
    data = load_manifest(root, tag.kind)
    version = str(data[tag.kind].get("version", ""))
    if version != tag.core:
        raise ReleaseError(
            f"version mismatch: tag {tag.core} vs {manifest_path(tag.kind)} {version}"
        )
    changelog_entry((root / "CHANGELOG.md").read_text(), tag.kind, tag.core)
    if repository and tag.kind != "bundle":
        expected = f"https://github.com/{repository}"
        actual = str(data[tag.kind].get("repository", ""))
        if actual != expected:
            raise ReleaseError(
                f"repository mismatch: manifest {actual} vs publishing repository {expected}"
            )
    if tag.kind == "bundle":
        for kind, pin in bundle_pins(data).items():
            if not CORE_RE.match(pin):
                raise ReleaseError(f"invalid pin: {kind} {pin} (must be X.Y.Z)")
    return {
        "kind": tag.kind,
        "version": tag.core,
        "tag": tag.name,
        "prerelease": tag.prerelease,
        "archive": tag.archive,
    }


def bundle_pins(data: dict) -> dict[str, str]:
    """Return {"preset": pin, "extension": pin} from a bundle manifest (one entry each)."""
    pins = {}
    for kind, key in (("preset", "presets"), ("extension", "extensions")):
        entries = [e for e in data.get(key) or [] if e.get("id") == "openproject"]
        if len(entries) != 1:
            raise ReleaseError(f"bundle must pin exactly one openproject {kind}")
        pins[kind] = str(entries[0].get("version", ""))
    return pins


def package_files(package_dir: Path) -> list[Path]:
    files = []
    for path in package_dir.rglob("*"):
        rel = path.relative_to(package_dir)
        if not path.is_file() or path.is_symlink():
            continue
        if any(part.startswith(".") or part == "__pycache__" for part in rel.parts):
            continue
        if path.suffix == ".pyc":
            continue
        files.append(rel)
    return sorted(files, key=lambda p: p.as_posix())


def build(root: Path, kind: str, out: Path, version: str | None = None) -> tuple[Path, str]:
    if version is None:
        version = str(load_manifest(root, kind)[kind]["version"])
    package_dir = root / kind
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"openproject-{kind}-{version}.zip"
    with zipfile.ZipFile(target, "w") as archive:
        for rel in package_files(package_dir):
            info = zipfile.ZipInfo(rel.as_posix(), date_time=ZIP_EPOCH)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (package_dir / rel).read_bytes())
    return target, sha256(target)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _host_allowed(host: str) -> bool:
    return any(host == allowed or host.endswith("." + allowed) for allowed in ALLOWED_HOSTS)


def archive_violations(path: Path) -> list[str]:
    violations = []
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if not any(name in names for name in ("preset.yml", "extension.yml")):
            violations.append("manifest missing at archive root")
        for name in names:
            parts = name.split("/")
            if name.startswith("/") or ".." in parts:
                violations.append(f"unsafe path: {name}")
            is_env = any(part == ".env" or part.startswith(".env.") for part in parts)
            if is_env or any(part in FORBIDDEN_COMPONENTS for part in parts[:-1]):
                violations.append(f"forbidden path: {name}")
            elif any(part.startswith(".") for part in parts if part):
                violations.append(f"hidden path: {name}")
            if name.endswith("/"):
                continue
            text = archive.read(name).decode("utf-8", errors="replace")
            if TOKEN_RE.search(text):
                violations.append(f"token-like string in {name}")
            for host in sorted({m.lower() for m in URL_HOST_RE.findall(text)}):
                if not _host_allowed(host):
                    violations.append(f"host not allowed in {name}: {host}")
    return violations


def publish_plan(
    tag: str, sha: str, marker: str | None, expected: list[str], present: list[str]
) -> dict:
    if marker is None and not present:
        return {"action": "create", "upload": list(expected)}
    if marker and marker == sha:
        missing = [name for name in expected if name not in present]
        return {"action": "upload" if missing else "noop", "upload": missing}
    raise ReleaseError(
        f"conflict: release {tag} was created from {marker or 'unknown'}, tag now points to {sha}"
    )


def _cmd_check(args: argparse.Namespace) -> int:
    print(json.dumps(check(ROOT, args.tag, args.repository)))
    return 0


def _cmd_notes(args: argparse.Namespace) -> int:
    sys.stdout.write(changelog_entry((ROOT / "CHANGELOG.md").read_text(), args.kind, args.version))
    return 0


def _cmd_build(args: argparse.Namespace) -> int:
    target, digest = build(ROOT, args.kind, Path(args.out), args.version)
    print(f"{target} {digest}")
    return 0


def _cmd_verify_archive(args: argparse.Namespace) -> int:
    violations = archive_violations(Path(args.zip))
    for violation in violations:
        print(f"release: {violation}", file=sys.stderr)
    return 1 if violations else 0


def _cmd_publish_plan(args: argparse.Namespace) -> int:
    plan = publish_plan(args.tag, args.sha, args.marker, args.expected, args.present)
    print(json.dumps(plan))
    return 0


def _not_implemented(args: argparse.Namespace) -> int:
    raise ReleaseError(f"{args.command}: not implemented")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="release.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check", help="gate a release tag (read-only)")
    p.add_argument("tag")
    p.add_argument("--repository", help="owner/repo of the publishing repository")
    p.set_defaults(func=_cmd_check)

    p = sub.add_parser("notes", help="print the changelog entry body")
    p.add_argument("kind", choices=KINDS)
    p.add_argument("version")
    p.set_defaults(func=_cmd_notes)

    p = sub.add_parser("build", help="build the reproducible package archive")
    p.add_argument("kind", choices=("preset", "extension"))
    p.add_argument("--out", default="dist")
    p.add_argument("--version", help="tag version incl. suffix (default: manifest version)")
    p.set_defaults(func=_cmd_build)

    p = sub.add_parser("verify-archive", help="check an archive against the layout rules")
    p.add_argument("zip")
    p.set_defaults(func=_cmd_verify_archive)

    p = sub.add_parser("bundle-catalog", help="write the one-entry catalogs for a bundle")
    p.add_argument("--bundle", default="bundle/bundle.yml")
    p.add_argument("--tag", required=True)
    p.add_argument("--archives", required=True)
    p.add_argument("--repository", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--download-base")
    p.set_defaults(func=_not_implemented)

    p = sub.add_parser("publish-plan", help="decide the publish action (stdlib only)")
    p.add_argument("--tag", required=True)
    p.add_argument("--sha", required=True)
    p.add_argument("--marker")
    p.add_argument("--expected", nargs="*", default=[])
    p.add_argument("--present", nargs="*", default=[])
    p.set_defaults(func=_cmd_publish_plan)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ReleaseError as exc:
        print(f"release: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
