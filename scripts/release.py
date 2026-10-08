#!/usr/bin/env python3
"""Release helper for the preset, extension and bundle packages (feature 006).

Contract: specs/006-release-engineering/contracts/release-script.md.

Exit codes: 0 ok, 1 a gate failed (message on stderr, prefixed ``release: ``), 2 usage error.
Uses the stdlib and PyYAML only. PyYAML is imported lazily so ``publish-plan`` runs on a bare
``python3``. No subcommand touches the network or writes outside ``--out``.
"""

from __future__ import annotations

import argparse
import re
import sys
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


def _not_implemented(args: argparse.Namespace) -> int:
    raise ReleaseError(f"{args.command}: not implemented")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="release.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check", help="gate a release tag (read-only)")
    p.add_argument("tag")
    p.add_argument("--repository", help="owner/repo of the publishing repository")
    p.set_defaults(func=_not_implemented)

    p = sub.add_parser("notes", help="print the changelog entry body")
    p.add_argument("kind", choices=KINDS)
    p.add_argument("version")
    p.set_defaults(func=_not_implemented)

    p = sub.add_parser("build", help="build the reproducible package archive")
    p.add_argument("kind", choices=("preset", "extension"))
    p.add_argument("--out", default="dist")
    p.add_argument("--version", help="tag version incl. suffix (default: manifest version)")
    p.set_defaults(func=_not_implemented)

    p = sub.add_parser("verify-archive", help="check an archive against the layout rules")
    p.add_argument("zip")
    p.set_defaults(func=_not_implemented)

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
    p.set_defaults(func=_not_implemented)

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
