# Catalog checklist: extension `openproject`

Upstream rules read on 2026-10-08 (research R9, T027):

- [G] https://github.com/github/spec-kit/blob/main/extensions/EXTENSION-PUBLISHING-GUIDE.md
- [T] https://github.com/github/spec-kit/blob/main/.github/ISSUE_TEMPLATE/extension_submission.yml

Every item has a state: `met`, `gap` (with options) or `n/a` (with reason). `tests/test_release.py` checks this (SC-006). Re-read both sources before filing; update this file if they changed.

## Requirements

| # | Requirement (source) | Evidence | State | Reason / options |
|---|----------------------|----------|-------|------------------|
| 1 | Valid `extension.yml` manifest included [T] | `extension/extension.yml`; `tests/test_manifests.py`; install test S26 (`docs/TESTING.md`) | met | |
| 2 | Extension id follows naming conventions (lowercase with hyphens) [G][T] | `extension.id: openproject` | met | No entry with id `openproject` in `extensions/catalog.community.json` on 2026-10-08 |
| 3 | Version is semantic [G] | `extension.version: 0.1.0` | met | |
| 4 | Description under 100 characters [G] (under 200 in [T]) | `extension/extension.yml` (85 characters) | met | Shortened on 2026-10-08 to meet the stricter guide limit |
| 5 | Author, license and repository in the manifest [G] | `Daniel Ring`, `MIT`, `https://github.com/Nachklang-io/speckit-openproject` | met | |
| 6 | Homepage (recommended) [G] | `homepage` in `docs/catalog/extension-entry.json` | met | Set in the catalog entry; the manifest has no `homepage` key |
| 7 | `requires.speckit_version` set [G] | `>=1.1.0`; CI installs on spec-kit v1.1.0 and v1.1.2 | met | |
| 8 | `provides.commands` lists every command, and the files exist and are formatted correctly [G][T] | 5 commands in `extension/commands/`; `tests/test_manifests.py` | met | |
| 9 | 2–5 tags [G] | `openproject`, `project-management`, `mcp` | met | |
| 10 | Required tools named [T] | `requires.tools` in `extension-entry.json`: `openproject-ce-mcp >=0.4.1` | met | The MCP server runs in the agent's MCP client config, not as a CLI; the entry says so in the submission text |
| 11 | README.md with installation and usage instructions [G][T] | `extension/README.md`: section "Install" and one section per command | met | |
| 12 | LICENSE file included [G][T] | `extension/LICENSE`, shipped at the archive root (`specs/006-release-engineering/contracts/archive-layout.md`) | met | |
| 13 | CHANGELOG (recommended) [G] | `CHANGELOG.md`, section "Extension" | met | One changelog for all packages, one section each |
| 14 | Download URL is a GitHub release archive for a version tag [G][T] | `https://github.com/Nachklang-io/speckit-openproject/releases/download/extension-v0.1.0/openproject-extension-0.1.0.zip` | met | Upstream shows `v1.0.0` and `archive/refs/tags/…` as an example only. Our tag is `extension-v0.1.0`, and the archive is a release asset with the manifest at the root (a source archive of the monorepo has two manifests in subdirectories) |
| 15 | GitHub release created with version tag [T] | Release `extension-v0.1.0` | gap | Not published yet. Options: (a) the maintainer pushes `extension-v0.1.0` on `main` after merge (T038), then files the submission (chosen); (b) file with the rc release (rejected: catalog entries should point at final versions) |
| 16 | `sha256` in the catalog entry matches the published archive (optional upstream) | `docs/catalog/extension-entry.json` | gap | Placeholder until item 15. Options: (a) after T038, copy the sha256 from `sha256sum` of the downloaded asset (chosen; see `submission.md`); (b) drop `sha256` (rejected because spec-kit verifies it on install) |
| 17 | Extension installs successfully via the download URL [T] | S26: `specify extension add openproject --from` against a local server, CI `install-smoke` on spec-kit v1.1.0 and v1.1.2 | met | The anonymous download from GitHub is checked in T035 (rc) and T038 (final) |
| 18 | All commands execute without errors [T] | `docs/TESTING.md` S10–S25 through the installed skills against the maintainer's test instance | met | Untested paths are listed per command in `extension/README.md` |
| 19 | Documentation is complete and accurate [T] | `extension/README.md` | met | |
| 20 | No security vulnerabilities identified [T] | ADR-0002 (MCP only, no REST calls), no tokens in files (CI secret check), reviewer subagents on every feature | met | |
| 21 | Tested on at least one real project [T] | `docs/TESTING.md` S10–S25 | met | |
| 22 | Submitted through the "Extension Submission" issue form, not a PR to `catalog.community.json` [G][T] | `docs/catalog/submission.md`, `docs/catalog/extension-entry.json` | met | Prepared, filed by the maintainer (FR-015) |
| 23 | Hooks declared [T] | `hooks.after_implement` → `speckit.openproject.sync-status`, optional | met | |

## Repository layout

The extension shares its repository with the preset (ADR-0001). The extension guide does not cover monorepos. Options:

1. Explain the layout in the submission (chosen): the release asset is a self-contained archive with `extension.yml` at its root, and the documentation link points to `extension/README.md`. The preset guide accepts the same layout explicitly.
2. Split the extension into its own repository with `git subtree split`, as ADR-0001 foresees, if a reviewer requires a root manifest. This is the maintainer's call.
