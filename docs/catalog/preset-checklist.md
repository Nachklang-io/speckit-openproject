# Catalog checklist: preset `openproject`

Upstream rules read on 2026-10-08 (research R9, T027):

- [P] https://github.com/github/spec-kit/blob/main/presets/PUBLISHING.md
- [T] https://github.com/github/spec-kit/blob/main/.github/ISSUE_TEMPLATE/preset_submission.yml

Every item has a state: `met`, `gap` (with options) or `n/a` (with reason). `tests/test_release.py` checks this (SC-006). Re-read both sources before filing; update this file if they changed.

## Requirements

| # | Requirement (source) | Evidence | State | Reason / options |
|---|----------------------|----------|-------|------------------|
| 1 | Valid `preset.yml` manifest included [T] | `preset/preset.yml`; `tests/test_manifests.py`; install test S26 (`docs/TESTING.md`) | met | |
| 2 | Preset id is lowercase with hyphens [P][T] | `preset.id: openproject` | met | No entry with id `openproject` in `presets/catalog.community.json` on 2026-10-08 |
| 3 | Version is semantic [P] | `preset.version: 1.0.0` | met | |
| 4 | Description under 200 characters [P][T] | `preset/preset.yml` (160 characters) | met | |
| 5 | 2–5 lowercase tags [P] | `openproject`, `issue-tracking`, `project-management`, `mcp`, `preset` | met | |
| 6 | Command names use dot notation [P] | `speckit.taskstoissues` | met | |
| 7 | Author, repository and license in the manifest [P] | `Daniel Ring`, `https://github.com/Nachklang-io/speckit-openproject`, `MIT` | met | |
| 8 | `requires.speckit_version` set [P] | `>=1.1.0`; CI installs on spec-kit v1.1.0 and v1.1.2 | met | |
| 9 | LICENSE file included [T] | `preset/LICENSE`, shipped at the archive root (`specs/006-release-engineering/contracts/archive-layout.md`) | met | |
| 10 | Linked README explains usage and contains a valid `specify preset add --from <download-url>` with the exact download URL [P][T] | `preset/README.md`, section "Install" | met | The URL resolves only once `preset-v1.0.0` is published (item 13) |
| 11 | Monorepo: the documentation link points to the README inside the preset directory, not the repository root [P] | `https://github.com/Nachklang-io/speckit-openproject/blob/preset-v1.0.0/preset/README.md` in `preset-entry.json` | met | See "Repository layout" below |
| 12 | Download URL is a GitHub release archive for a version tag [P][T] | `https://github.com/Nachklang-io/speckit-openproject/releases/download/preset-v1.0.0/openproject-preset-1.0.0.zip` | met | Upstream shows `v1.0.0` and `archive/refs/tags/…` as an example only. Our tag is `preset-v1.0.0`, and the archive is a release asset with the manifest at the root (spec-kit refuses a source archive of the monorepo, which has two manifests in subdirectories) |
| 13 | GitHub release created with version tag [T] | Release `preset-v1.0.0` (https://github.com/Nachklang-io/speckit-openproject/releases/tag/preset-v1.0.0) | met | Published 2026-10-08 (S33) |
| 14 | `sha256` in the catalog entry matches the published archive | `docs/catalog/preset-entry.json` | met | Matches the release asset digest `e645436e…cc84` (checked 2026-10-08) |
| 15 | Preset installs via `specify preset add` [P][T] | S26: `specify preset add --from` against a local server, CI `install-smoke` on spec-kit v1.1.0 and v1.1.2 | met | The anonymous download from GitHub is checked in T035 (rc) and T038 (final) |
| 16 | Template resolution works after install (`specify preset resolve spec-template`) [P][T] | `provides.templates` has only a command override | n/a | The preset provides no templates; `spec-template` keeps resolving to the core template. The command override is item 17 |
| 17 | Provided commands are registered in the agent directories after install [P] | S26: skill `speckit-taskstoissues` carries `preset:openproject` | met | |
| 18 | Documentation is complete and accurate [T] | `preset/README.md`: prerequisites, install, usage, behavior, untested paths, limitations | met | |
| 19 | Tested on at least one real project [T] | `docs/TESTING.md` S1–S9 against the maintainer's OpenProject test instance | met | |
| 20 | Submission prepared: catalog entry and `docs/community/presets.md` row [P], or the issue form [T] | `docs/catalog/preset-entry.json`, `docs/catalog/submission.md` | met | Filed by the maintainer (FR-015). The guides disagree about PR vs issue form; `submission.md` gives both, the issue form first |

## Repository layout

Preset and extension share one repository (ADR-0001). PUBLISHING.md allows this explicitly: "link the README inside that directory (`presets/<id>/README.md`) rather than the repository-root README". Options if a reviewer still objects:

1. Explain the layout in the submission (chosen): the release asset is a self-contained archive with `preset.yml` at its root, and the documentation link points to `preset/README.md`.
2. Split the preset into its own repository with `git subtree split`, as ADR-0001 foresees. This keeps history, but it needs a new repository and a change to the `repository` field, which is the maintainer's call.
